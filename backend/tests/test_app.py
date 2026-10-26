import base64
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.previous_username = os.environ.get("ARKPEDRA_ADMIN_USERNAME")
        self.previous_password = os.environ.get("ARKPEDRA_ADMIN_PASSWORD")
        self.previous_secret = os.environ.get("ARKPEDRA_SECRET_KEY")
        self.previous_environment = os.environ.get("ARKPEDRA_ENV")
        os.environ["ARKPEDRA_ADMIN_USERNAME"] = "gestor-de-teste"
        os.environ["ARKPEDRA_ADMIN_PASSWORD"] = "senha-de-teste"
        os.environ["ARKPEDRA_SECRET_KEY"] = "segredo-exclusivo-dos-testes"
        os.environ["ARKPEDRA_ENV"] = "development"
        app = create_app(
            Path(self.temp_directory.name) / "arkpedra.db",
            Path(self.temp_directory.name) / "uploads",
        )
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        self.temp_directory.cleanup()
        if self.previous_username is None:
            os.environ.pop("ARKPEDRA_ADMIN_USERNAME", None)
        else:
            os.environ["ARKPEDRA_ADMIN_USERNAME"] = self.previous_username
        if self.previous_password is None:
            os.environ.pop("ARKPEDRA_ADMIN_PASSWORD", None)
        else:
            os.environ["ARKPEDRA_ADMIN_PASSWORD"] = self.previous_password
        if self.previous_secret is None:
            os.environ.pop("ARKPEDRA_SECRET_KEY", None)
        else:
            os.environ["ARKPEDRA_SECRET_KEY"] = self.previous_secret
        if self.previous_environment is None:
            os.environ.pop("ARKPEDRA_ENV", None)
        else:
            os.environ["ARKPEDRA_ENV"] = self.previous_environment

    def login(self):
        response = self.client.post(
            "/api/admin/login",
            json={"username": "gestor-de-teste", "password": "senha-de-teste"},
        )
        self.assertEqual(response.status_code, 200)

    def test_public_health_and_configuration(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/favicon.ico").status_code, 200)
        response = self.client.get("/api/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.json()["stones"][0]["name"], "Granito escuro")
        self.assertNotIn("id", response.json()["stones"][0])

    def test_admin_requires_login_and_rejects_wrong_password(self):
        self.assertEqual(self.client.get("/api/admin/config").status_code, 401)
        wrong_login = self.client.post(
            "/api/admin/login",
            json={"username": "gestor-de-teste", "password": "errada"},
        )
        self.assertEqual(wrong_login.status_code, 401)
        wrong_user = self.client.post(
            "/api/admin/login",
            json={"username": "outro", "password": "senha-de-teste"},
        )
        self.assertEqual(wrong_user.status_code, 401)

    def test_owner_can_update_price(self):
        self.login()
        stone = self.client.get("/api/admin/config").json()["stones"][0]
        response = self.client.put(
            f"/api/admin/stones/{stone['id']}",
            json={
                "name": stone["name"],
                "description": stone["description"],
                "price_per_m2": 612.75,
                "active": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["price_per_m2"], 612.75)
        self.assertEqual(self.client.get("/api/config").json()["stones"][0]["price_per_m2"], 612.75)

    def test_rejects_invalid_image_file(self):
        self.login()
        stone = self.client.get("/api/admin/config").json()["stones"][0]
        response = self.client.post(
            f"/api/admin/stones/{stone['id']}/image",
            files={"file": ("not-an-image.txt", b"plain text", "text/plain")},
        )

        self.assertEqual(response.status_code, 415)

    def test_owner_can_upload_site_image(self):
        self.login()
        one_pixel_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        response = self.client.post(
            "/api/admin/images/process",
            data={"alt_text": "Detalhe da medição"},
            files={"file": ("medicao.png", one_pixel_png, "image/png")},
        )

        self.assertEqual(response.status_code, 200)
        image_url = response.json()["url"]
        self.assertTrue(image_url.startswith("/uploads/process-"))
        self.assertEqual(self.client.get(image_url).status_code, 200)
        public_image = self.client.get("/api/config").json()["images"]["process"]
        self.assertEqual(public_image["alt_text"], "Detalhe da medição")

    def test_owner_can_create_and_delete_stone(self):
        self.login()
        created = self.client.post(
            "/api/admin/stones",
            json={
                "name": "Quartzito azul",
                "description": "Veios marcantes",
                "price_per_m2": 1450,
                "active": True,
            },
        )

        self.assertEqual(created.status_code, 201)
        stone_id = created.json()["id"]
        public_names = {stone["name"] for stone in self.client.get("/api/config").json()["stones"]}
        self.assertIn("Quartzito azul", public_names)
        self.assertEqual(self.client.delete(f"/api/admin/stones/{stone_id}").status_code, 204)

    def test_owner_can_create_and_delete_pricing_option(self):
        self.login()
        created = self.client.post(
            "/api/admin/options",
            json={"category": "finish", "label": "Borda bisotada", "value": 135, "active": True},
        )

        self.assertEqual(created.status_code, 201)
        option_id = created.json()["id"]
        public_labels = {
            option["label"] for option in self.client.get("/api/config").json()["options"]["finish"]
        }
        self.assertIn("Borda bisotada", public_labels)
        self.assertEqual(self.client.delete(f"/api/admin/options/{option_id}").status_code, 204)

    def test_production_disables_api_documentation(self):
        os.environ["ARKPEDRA_ENV"] = "production"
        production_app = create_app(
            Path(self.temp_directory.name) / "production.db",
            Path(self.temp_directory.name) / "production-uploads",
        )
        with TestClient(production_app) as production_client:
            self.assertEqual(production_client.get("/docs").status_code, 404)
            self.assertEqual(production_client.get("/redoc").status_code, 404)
            self.assertEqual(production_client.get("/openapi.json").status_code, 404)

    def test_production_rejects_default_credentials(self):
        os.environ["ARKPEDRA_ENV"] = "production"
        os.environ["ARKPEDRA_ADMIN_USERNAME"] = "admin"
        os.environ["ARKPEDRA_ADMIN_PASSWORD"] = "arkpedra"
        with self.assertRaisesRegex(RuntimeError, "administrativos próprios"):
            create_app(
                Path(self.temp_directory.name) / "unsafe.db",
                Path(self.temp_directory.name) / "unsafe-uploads",
            )


if __name__ == "__main__":
    unittest.main()
