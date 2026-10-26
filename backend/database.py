from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


STONE_SEEDS = (
    ("granito-escuro", "Granito escuro", "Resistente e versátil", 480.0, 1, 10),
    ("quartzo-branco", "Quartzo branco", "Claro e uniforme", 920.0, 1, 20),
    ("marmore-claro", "Mármore claro", "Veios delicados", 760.0, 1, 30),
    ("pedra-exotica", "Pedra exótica", "Desenho marcante", 1180.0, 1, 40),
)

OPTION_SEEDS = (
    ("sink", "sem-cuba", "Sem cuba", 0.0, 1, 0, 10),
    ("sink", "recorte-cliente", "Recorte para cuba do cliente", 180.0, 1, 0, 20),
    ("sink", "cuba-inox", "Cuba inox simples", 650.0, 1, 1, 30),
    ("sink", "cuba-gourmet", "Cuba gourmet", 1100.0, 1, 0, 40),
    ("backsplash", "sem-frontao", "Sem frontão", 0.0, 1, 0, 10),
    ("backsplash", "frontao-10", "10 cm", 10.0, 1, 1, 20),
    ("backsplash", "frontao-15", "15 cm", 15.0, 1, 0, 30),
    ("backsplash", "frontao-20", "20 cm", 20.0, 1, 0, 40),
    ("finish", "reto-polido", "Reto polido", 40.0, 1, 0, 10),
    ("finish", "meia-esquadria", "Meia esquadria", 85.0, 1, 1, 20),
    ("finish", "boleado", "Boleado", 110.0, 1, 0, 30),
    ("installation", "com-instalacao", "Incluir instalação", 320.0, 1, 1, 10),
    ("installation", "somente-fornecimento", "Somente fornecimento", 0.0, 1, 0, 20),
)

IMAGE_SEEDS = (
    ("hero", "Imagem principal", "assets/images/arkpedra-slab-workshop.webp", "Chapa de pedra em uma oficina de marmoraria"),
    ("stone_archive", "Catálogo de pedras", "assets/images/arkpedra-stone-archive.webp", "Amostras de granito, quartzito e mármore"),
    ("process", "Processo de medição", "assets/images/arkpedra-measuring.webp", "Profissional medindo uma bancada de pedra"),
    ("result", "Ambiente finalizado", "assets/images/arkpedra-kitchen.webp", "Cozinha com bancada de quartzito verde"),
)

OPTION_CATEGORIES = {"sink", "backsplash", "finish", "installation"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "item"


class ArkPedraDatabase:
    def __init__(self, path: Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS stones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price_per_m2 REAL NOT NULL CHECK(price_per_m2 >= 0),
                    image_path TEXT,
                    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pricing_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    option_key TEXT NOT NULL,
                    label TEXT NOT NULL,
                    value REAL NOT NULL CHECK(value >= 0),
                    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                    is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0, 1)),
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    UNIQUE(category, option_key)
                );

                CREATE TABLE IF NOT EXISTS site_images (
                    slot TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    path TEXT NOT NULL,
                    alt_text TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._seed_if_empty(connection)

    def _seed_if_empty(self, connection: sqlite3.Connection) -> None:
        now = utc_now()
        if connection.execute("SELECT COUNT(*) FROM stones").fetchone()[0] == 0:
            connection.executemany(
                """
                INSERT INTO stones
                    (slug, name, description, price_per_m2, active, sort_order, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [row + (now,) for row in STONE_SEEDS],
            )

        if connection.execute("SELECT COUNT(*) FROM pricing_options").fetchone()[0] == 0:
            connection.executemany(
                """
                INSERT INTO pricing_options
                    (category, option_key, label, value, active, is_default, sort_order, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [row + (now,) for row in OPTION_SEEDS],
            )

        if connection.execute("SELECT COUNT(*) FROM site_images").fetchone()[0] == 0:
            connection.executemany(
                """
                INSERT INTO site_images (slot, label, path, alt_text, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [row + (now,) for row in IMAGE_SEEDS],
            )

    @staticmethod
    def _rows(rows: Iterable[sqlite3.Row]) -> List[Dict[str, Any]]:
        return [dict(row) for row in rows]

    @staticmethod
    def _unique_value(
        connection: sqlite3.Connection,
        table: str,
        column: str,
        base: str,
        category: Optional[str] = None,
    ) -> str:
        candidate = base
        suffix = 2
        while True:
            if category is None:
                row = connection.execute(
                    f"SELECT 1 FROM {table} WHERE {column} = ?", (candidate,)
                ).fetchone()
            else:
                row = connection.execute(
                    f"SELECT 1 FROM {table} WHERE category = ? AND {column} = ?",
                    (category, candidate),
                ).fetchone()
            if row is None:
                return candidate
            candidate = f"{base}-{suffix}"
            suffix += 1

    def get_config(self, include_inactive: bool = False) -> Dict[str, Any]:
        active_filter = "" if include_inactive else "WHERE active = 1"
        with self.connect() as connection:
            stones = self._rows(
                connection.execute(
                    f"SELECT * FROM stones {active_filter} ORDER BY sort_order, id"
                ).fetchall()
            )
            options = self._rows(
                connection.execute(
                    f"SELECT * FROM pricing_options {active_filter} ORDER BY category, sort_order, id"
                ).fetchall()
            )
            images = self._rows(
                connection.execute("SELECT * FROM site_images ORDER BY slot").fetchall()
            )

        grouped_options: Dict[str, List[Dict[str, Any]]] = {}
        for option in options:
            grouped_options.setdefault(option["category"], []).append(option)

        return {
            "stones": stones,
            "options": grouped_options,
            "images": {image["slot"]: image for image in images},
        }

    def update_stone(
        self,
        stone_id: int,
        name: str,
        description: str,
        price_per_m2: float,
        active: bool,
    ) -> Dict[str, Any]:
        if not name.strip():
            raise ValueError("Informe o nome da pedra.")
        if price_per_m2 < 0:
            raise ValueError("O preço não pode ser negativo.")

        with self.connect() as connection:
            current = connection.execute("SELECT * FROM stones WHERE id = ?", (stone_id,)).fetchone()
            if current is None:
                raise KeyError("Pedra não encontrada.")
            if current["active"] and not active:
                active_count = connection.execute("SELECT COUNT(*) FROM stones WHERE active = 1").fetchone()[0]
                if active_count <= 1:
                    raise ValueError("Mantenha pelo menos uma pedra ativa.")

            connection.execute(
                """
                UPDATE stones
                SET name = ?, description = ?, price_per_m2 = ?, active = ?, updated_at = ?
                WHERE id = ?
                """,
                (name.strip(), description.strip(), price_per_m2, int(active), utc_now(), stone_id),
            )
            row = connection.execute("SELECT * FROM stones WHERE id = ?", (stone_id,)).fetchone()
        return dict(row)

    def create_stone(
        self,
        name: str,
        description: str,
        price_per_m2: float,
        active: bool = True,
    ) -> Dict[str, Any]:
        if not name.strip():
            raise ValueError("Informe o nome da pedra.")
        if price_per_m2 < 0:
            raise ValueError("O preço não pode ser negativo.")

        with self.connect() as connection:
            slug = self._unique_value(connection, "stones", "slug", slugify(name))
            sort_order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), 0) + 10 FROM stones"
            ).fetchone()[0]
            cursor = connection.execute(
                """
                INSERT INTO stones
                    (slug, name, description, price_per_m2, active, sort_order, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slug,
                    name.strip(),
                    description.strip(),
                    price_per_m2,
                    int(active),
                    sort_order,
                    utc_now(),
                ),
            )
            row = connection.execute(
                "SELECT * FROM stones WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def delete_stone(self, stone_id: int) -> Dict[str, Any]:
        with self.connect() as connection:
            current = connection.execute("SELECT * FROM stones WHERE id = ?", (stone_id,)).fetchone()
            if current is None:
                raise KeyError("Pedra não encontrada.")
            total = connection.execute("SELECT COUNT(*) FROM stones").fetchone()[0]
            active_count = connection.execute("SELECT COUNT(*) FROM stones WHERE active = 1").fetchone()[0]
            if total <= 1 or (current["active"] and active_count <= 1):
                raise ValueError("Mantenha pelo menos uma pedra ativa.")
            connection.execute("DELETE FROM stones WHERE id = ?", (stone_id,))
        return dict(current)

    def set_stone_image(self, stone_id: int, image_path: str) -> Dict[str, Any]:
        with self.connect() as connection:
            exists = connection.execute("SELECT 1 FROM stones WHERE id = ?", (stone_id,)).fetchone()
            if exists is None:
                raise KeyError("Pedra não encontrada.")
            connection.execute(
                "UPDATE stones SET image_path = ?, updated_at = ? WHERE id = ?",
                (image_path, utc_now(), stone_id),
            )
            row = connection.execute("SELECT * FROM stones WHERE id = ?", (stone_id,)).fetchone()
        return dict(row)

    def update_option(
        self,
        option_id: int,
        label: str,
        value: float,
        active: bool,
    ) -> Dict[str, Any]:
        if not label.strip():
            raise ValueError("Informe o nome da opção.")
        if value < 0:
            raise ValueError("O valor não pode ser negativo.")

        with self.connect() as connection:
            current = connection.execute(
                "SELECT * FROM pricing_options WHERE id = ?", (option_id,)
            ).fetchone()
            if current is None:
                raise KeyError("Opção não encontrada.")
            if current["active"] and not active:
                active_count = connection.execute(
                    "SELECT COUNT(*) FROM pricing_options WHERE category = ? AND active = 1",
                    (current["category"],),
                ).fetchone()[0]
                if active_count <= 1:
                    raise ValueError("Mantenha pelo menos uma opção ativa neste grupo.")

            connection.execute(
                """
                UPDATE pricing_options
                SET label = ?, value = ?, active = ?, updated_at = ?
                WHERE id = ?
                """,
                (label.strip(), value, int(active), utc_now(), option_id),
            )
            row = connection.execute(
                "SELECT * FROM pricing_options WHERE id = ?", (option_id,)
            ).fetchone()
        return dict(row)

    def create_option(
        self,
        category: str,
        label: str,
        value: float,
        active: bool = True,
    ) -> Dict[str, Any]:
        if category not in OPTION_CATEGORIES:
            raise ValueError("Grupo de valores inválido.")
        if not label.strip():
            raise ValueError("Informe o nome da opção.")
        if value < 0:
            raise ValueError("O valor não pode ser negativo.")

        with self.connect() as connection:
            option_key = self._unique_value(
                connection,
                "pricing_options",
                "option_key",
                slugify(label),
                category,
            )
            sort_order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), 0) + 10 FROM pricing_options WHERE category = ?",
                (category,),
            ).fetchone()[0]
            cursor = connection.execute(
                """
                INSERT INTO pricing_options
                    (category, option_key, label, value, active, is_default, sort_order, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (category, option_key, label.strip(), value, int(active), sort_order, utc_now()),
            )
            row = connection.execute(
                "SELECT * FROM pricing_options WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def delete_option(self, option_id: int) -> Dict[str, Any]:
        with self.connect() as connection:
            current = connection.execute(
                "SELECT * FROM pricing_options WHERE id = ?", (option_id,)
            ).fetchone()
            if current is None:
                raise KeyError("Opção não encontrada.")
            active_count = connection.execute(
                "SELECT COUNT(*) FROM pricing_options WHERE category = ? AND active = 1",
                (current["category"],),
            ).fetchone()[0]
            if current["active"] and active_count <= 1:
                raise ValueError("Mantenha pelo menos uma opção ativa neste grupo.")

            connection.execute("DELETE FROM pricing_options WHERE id = ?", (option_id,))
            if current["is_default"]:
                replacement = connection.execute(
                    """
                    SELECT id FROM pricing_options
                    WHERE category = ? AND active = 1
                    ORDER BY sort_order, id LIMIT 1
                    """,
                    (current["category"],),
                ).fetchone()
                if replacement:
                    connection.execute(
                        "UPDATE pricing_options SET is_default = 1 WHERE id = ?",
                        (replacement["id"],),
                    )
        return dict(current)

    def set_site_image(self, slot: str, image_path: str, alt_text: str) -> Dict[str, Any]:
        with self.connect() as connection:
            current = connection.execute("SELECT * FROM site_images WHERE slot = ?", (slot,)).fetchone()
            if current is None:
                raise KeyError("Espaço de imagem não encontrado.")
            connection.execute(
                """
                UPDATE site_images
                SET path = ?, alt_text = ?, updated_at = ?
                WHERE slot = ?
                """,
                (image_path, alt_text.strip(), utc_now(), slot),
            )
            row = connection.execute("SELECT * FROM site_images WHERE slot = ?", (slot,)).fetchone()
        return dict(row)
