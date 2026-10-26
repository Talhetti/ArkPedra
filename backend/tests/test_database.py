import tempfile
import unittest
from pathlib import Path

from backend.database import ArkPedraDatabase


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = ArkPedraDatabase(Path(self.temp_directory.name) / "arkpedra.db")
        self.database.initialize()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_seeds_current_simulator_configuration(self):
        configuration = self.database.get_config()

        self.assertEqual(len(configuration["stones"]), 4)
        self.assertEqual(configuration["stones"][0]["price_per_m2"], 480.0)
        self.assertEqual(len(configuration["options"]["sink"]), 4)
        self.assertIn("hero", configuration["images"])

    def test_updates_stone_without_changing_its_identity(self):
        stone = self.database.get_config()["stones"][0]
        updated = self.database.update_stone(
            stone["id"], "Granito São Gabriel", "Escuro e resistente", 535.5, True
        )

        self.assertEqual(updated["slug"], stone["slug"])
        self.assertEqual(updated["name"], "Granito São Gabriel")
        self.assertEqual(updated["price_per_m2"], 535.5)

    def test_prevents_disabling_last_active_item(self):
        stones = self.database.get_config()["stones"]
        for stone in stones[:-1]:
            self.database.update_stone(
                stone["id"], stone["name"], stone["description"], stone["price_per_m2"], False
            )

        last = stones[-1]
        with self.assertRaisesRegex(ValueError, "pelo menos uma pedra"):
            self.database.update_stone(
                last["id"], last["name"], last["description"], last["price_per_m2"], False
            )

    def test_creates_unique_stones_and_deletes_them(self):
        first = self.database.create_stone("Quartzito Azul", "Veios azuis", 1450, True)
        second = self.database.create_stone("Quartzito Azul", "Outra chapa", 1500, True)

        self.assertEqual(first["slug"], "quartzito-azul")
        self.assertEqual(second["slug"], "quartzito-azul-2")
        self.database.delete_stone(second["id"])
        ids = {stone["id"] for stone in self.database.get_config(include_inactive=True)["stones"]}
        self.assertNotIn(second["id"], ids)

    def test_creates_and_deletes_pricing_option(self):
        option = self.database.create_option("finish", "Borda bisotada", 135, True)

        self.assertEqual(option["option_key"], "borda-bisotada")
        self.database.delete_option(option["id"])
        ids = {
            item["id"]
            for item in self.database.get_config(include_inactive=True)["options"]["finish"]
        }
        self.assertNotIn(option["id"], ids)


if __name__ == "__main__":
    unittest.main()
