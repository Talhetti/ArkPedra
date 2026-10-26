from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import ArkPedraDatabase


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = ROOT / "backend" / "data" / "arkpedra.db"
UPLOAD_DIRECTORY = ROOT / "uploads"
ADMIN_DIRECTORY = ROOT / "admin"
COOKIE_NAME = "arkpedra_admin"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
IMAGE_SLOTS = {"hero", "stone_archive", "process", "result"}


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class StonePayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=180)
    price_per_m2: float = Field(ge=0, le=1_000_000)
    active: bool = True


class OptionPayload(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    value: float = Field(ge=0, le=1_000_000)
    active: bool = True


class OptionCreatePayload(OptionPayload):
    category: Literal["sink", "backsplash", "finish", "installation"]


def image_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return path if path.startswith("/") else f"/{path}"


def serialize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    for stone in config["stones"]:
        stone["image_url"] = image_url(stone.get("image_path"))
        stone["active"] = bool(stone["active"])
    for options in config["options"].values():
        for option in options:
            option["active"] = bool(option["active"])
            option["is_default"] = bool(option["is_default"])
    for site_image in config["images"].values():
        site_image["url"] = image_url(site_image["path"])
    return config


def serialize_public_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "stones": [
            {
                "name": stone["name"],
                "description": stone["description"],
                "price_per_m2": stone["price_per_m2"],
                "image_url": image_url(stone.get("image_path")),
            }
            for stone in config["stones"]
        ],
        "options": {
            category: [
                {
                    "label": option["label"],
                    "value": option["value"],
                    "is_default": bool(option["is_default"]),
                }
                for option in options
            ]
            for category, options in config["options"].items()
        },
        "images": {
            slot: {
                "label": site_image["label"],
                "url": image_url(site_image["path"]),
                "alt_text": site_image["alt_text"],
            }
            for slot, site_image in config["images"].items()
        },
    }


def detect_extension(content: bytes) -> Optional[str]:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def create_app(
    database_path: Optional[Path] = None,
    upload_directory: Optional[Path] = None,
) -> FastAPI:
    db_path = Path(database_path or os.getenv("ARKPEDRA_DATABASE_PATH", DEFAULT_DATABASE_PATH))
    database = ArkPedraDatabase(db_path)
    uploads_path = Path(upload_directory or UPLOAD_DIRECTORY)
    uploads_path.mkdir(parents=True, exist_ok=True)

    admin_username = os.getenv("ARKPEDRA_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ARKPEDRA_ADMIN_PASSWORD", "arkpedra")
    secret_key = os.getenv("ARKPEDRA_SECRET_KEY", "arkpedra-local-development-secret")
    environment = os.getenv("ARKPEDRA_ENV", "development").lower()
    is_production = environment == "production"
    using_default_credentials = admin_username == "admin" or admin_password == "arkpedra"
    if is_production and using_default_credentials:
        raise RuntimeError("Defina usuário e senha administrativos próprios antes de iniciar em produção.")
    secure_cookie = os.getenv("ARKPEDRA_COOKIE_SECURE", "1" if is_production else "0") == "1"

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.initialize()
        yield

    application = FastAPI(
        title="ArkPedra API",
        version="1.0.0",
        description="Configuração de preços e imagens do simulador ArkPedra.",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )
    application.state.database = database

    application.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")
    application.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")
    application.mount("/admin-assets", StaticFiles(directory=ADMIN_DIRECTORY), name="admin-assets")

    def expected_session_token() -> str:
        session_subject = f"arkpedra-owner:{admin_username}".encode()
        return hmac.new(secret_key.encode(), session_subject, hashlib.sha256).hexdigest()

    def require_admin(request: Request) -> None:
        supplied = request.cookies.get(COOKIE_NAME, "")
        if not supplied or not secrets.compare_digest(supplied, expected_session_token()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Faça login para continuar.")

    async def save_upload(upload: UploadFile, prefix: str) -> str:
        content = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="A imagem deve ter no máximo 5 MB.")
        extension = detect_extension(content)
        if extension is None:
            raise HTTPException(status_code=415, detail="Envie uma imagem PNG, JPG ou WebP.")
        filename = f"{prefix}-{secrets.token_hex(8)}{extension}"
        destination = uploads_path / filename
        destination.write_bytes(content)
        return f"uploads/{filename}"

    def database_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(status_code=404, detail=str(exc).strip("'"))
        return HTTPException(status_code=400, detail=str(exc))

    @application.get("/", include_in_schema=False)
    async def landing_page() -> FileResponse:
        return FileResponse(ROOT / "arkpedra.html")

    @application.get("/styles.css", include_in_schema=False)
    async def landing_styles() -> FileResponse:
        return FileResponse(ROOT / "styles.css", media_type="text/css")

    @application.get("/script.js", include_in_schema=False)
    async def landing_script() -> FileResponse:
        return FileResponse(ROOT / "script.js", media_type="application/javascript")

    @application.get("/pricing.js", include_in_schema=False)
    async def pricing_script() -> FileResponse:
        return FileResponse(ROOT / "pricing.js", media_type="application/javascript")

    @application.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> FileResponse:
        return FileResponse(ROOT / "assets" / "favicon.svg", media_type="image/svg+xml")

    @application.get("/admin", include_in_schema=False)
    async def admin_page() -> FileResponse:
        return FileResponse(ADMIN_DIRECTORY / "admin.html")

    @application.get("/api/health", tags=["system"])
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/config", tags=["public"])
    async def public_config(response: Response) -> Dict[str, Any]:
        response.headers["Cache-Control"] = "no-store"
        return serialize_public_config(database.get_config(include_inactive=False))

    @application.post("/api/admin/login", tags=["admin"])
    async def login(payload: LoginPayload) -> JSONResponse:
        valid_username = secrets.compare_digest(payload.username, admin_username)
        valid_password = secrets.compare_digest(payload.password, admin_password)
        if not valid_username or not valid_password:
            raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
        response = JSONResponse(
            {"authenticated": True, "using_default_credentials": using_default_credentials}
        )
        response.set_cookie(
            COOKIE_NAME,
            expected_session_token(),
            max_age=8 * 60 * 60,
            httponly=True,
            samesite="strict",
            secure=secure_cookie,
        )
        return response

    @application.post("/api/admin/logout", tags=["admin"])
    async def logout(_: None = Depends(require_admin)) -> JSONResponse:
        response = JSONResponse({"authenticated": False})
        response.delete_cookie(COOKIE_NAME)
        return response

    @application.get("/api/admin/session", tags=["admin"])
    async def session(_: None = Depends(require_admin)) -> Dict[str, Any]:
        return {
            "authenticated": True,
            "using_default_credentials": using_default_credentials,
        }

    @application.get("/api/admin/config", tags=["admin"])
    async def admin_config(_: None = Depends(require_admin)) -> Dict[str, Any]:
        return serialize_config(database.get_config(include_inactive=True))

    @application.post("/api/admin/stones", tags=["admin"], status_code=201)
    async def create_stone(
        payload: StonePayload,
        _: None = Depends(require_admin),
    ) -> Dict[str, Any]:
        try:
            stone = database.create_stone(
                payload.name,
                payload.description,
                payload.price_per_m2,
                payload.active,
            )
        except ValueError as exc:
            raise database_error(exc) from exc
        stone["active"] = bool(stone["active"])
        stone["image_url"] = image_url(stone.get("image_path"))
        return stone

    @application.put("/api/admin/stones/{stone_id}", tags=["admin"])
    async def update_stone(
        stone_id: int,
        payload: StonePayload,
        _: None = Depends(require_admin),
    ) -> Dict[str, Any]:
        try:
            stone = database.update_stone(
                stone_id,
                payload.name,
                payload.description,
                payload.price_per_m2,
                payload.active,
            )
        except (KeyError, ValueError) as exc:
            raise database_error(exc) from exc
        stone["active"] = bool(stone["active"])
        stone["image_url"] = image_url(stone.get("image_path"))
        return stone

    @application.post("/api/admin/stones/{stone_id}/image", tags=["admin"])
    async def update_stone_image(
        stone_id: int,
        file: UploadFile = File(...),
        _: None = Depends(require_admin),
    ) -> Dict[str, Any]:
        image_path = await save_upload(file, f"stone-{stone_id}")
        try:
            stone = database.set_stone_image(stone_id, image_path)
        except KeyError as exc:
            raise database_error(exc) from exc
        stone["active"] = bool(stone["active"])
        stone["image_url"] = image_url(stone.get("image_path"))
        return stone

    @application.delete("/api/admin/stones/{stone_id}", tags=["admin"], status_code=204)
    async def delete_stone(
        stone_id: int,
        _: None = Depends(require_admin),
    ) -> Response:
        try:
            database.delete_stone(stone_id)
        except (KeyError, ValueError) as exc:
            raise database_error(exc) from exc
        return Response(status_code=204)

    @application.post("/api/admin/options", tags=["admin"], status_code=201)
    async def create_option(
        payload: OptionCreatePayload,
        _: None = Depends(require_admin),
    ) -> Dict[str, Any]:
        try:
            option = database.create_option(
                payload.category,
                payload.label,
                payload.value,
                payload.active,
            )
        except ValueError as exc:
            raise database_error(exc) from exc
        option["active"] = bool(option["active"])
        option["is_default"] = bool(option["is_default"])
        return option

    @application.put("/api/admin/options/{option_id}", tags=["admin"])
    async def update_option(
        option_id: int,
        payload: OptionPayload,
        _: None = Depends(require_admin),
    ) -> Dict[str, Any]:
        try:
            option = database.update_option(option_id, payload.label, payload.value, payload.active)
        except (KeyError, ValueError) as exc:
            raise database_error(exc) from exc
        option["active"] = bool(option["active"])
        option["is_default"] = bool(option["is_default"])
        return option

    @application.delete("/api/admin/options/{option_id}", tags=["admin"], status_code=204)
    async def delete_option(
        option_id: int,
        _: None = Depends(require_admin),
    ) -> Response:
        try:
            database.delete_option(option_id)
        except (KeyError, ValueError) as exc:
            raise database_error(exc) from exc
        return Response(status_code=204)

    @application.post("/api/admin/images/{slot}", tags=["admin"])
    async def update_site_image(
        slot: str,
        file: UploadFile = File(...),
        alt_text: str = Form(default=""),
        _: None = Depends(require_admin),
    ) -> Dict[str, Any]:
        if slot not in IMAGE_SLOTS:
            raise HTTPException(status_code=404, detail="Espaço de imagem não encontrado.")
        if len(alt_text) > 250:
            raise HTTPException(status_code=400, detail="O texto alternativo deve ter até 250 caracteres.")
        image_path = await save_upload(file, slot)
        try:
            site_image = database.set_site_image(slot, image_path, alt_text)
        except KeyError as exc:
            raise database_error(exc) from exc
        site_image["url"] = image_url(site_image["path"])
        return site_image

    return application


app = create_app()
