import os
import bcrypt
import psycopg2
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("Переменная окружения DATABASE_URL не задана")
    return psycopg2.connect(DATABASE_URL)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s;
        """,
        (table, column),
    )
    return cur.fetchone() is not None


def ensure_tables_exist():
    """Создаёт таблицы, если их нет, и мигрирует старую схему к актуальной."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # --- users ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL
            );
            """
        )

        if not _column_exists(cur, "users", "password_hash"):
            cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);")

            if _column_exists(cur, "users", "password"):
                cur.execute("SELECT id, password FROM users WHERE password IS NOT NULL;")
                rows = cur.fetchall()
                for user_id, plain_password in rows:
                    hashed = hash_password(plain_password)
                    cur.execute(
                        "UPDATE users SET password_hash = %s WHERE id = %s;",
                        (hashed, user_id),
                    )
                cur.execute("ALTER TABLE users DROP COLUMN password;")

            cur.execute("ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;")

        # --- favorites ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                user_id VARCHAR(100) PRIMARY KEY
            );
            """
        )

        if not _column_exists(cur, "favorites", "favorite_ids"):
            cur.execute("ALTER TABLE favorites ADD COLUMN favorite_ids INTEGER[];")

            if _column_exists(cur, "favorites", "heroes"):
                cur.execute("ALTER TABLE favorites DROP COLUMN heroes;")

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка создания/миграции таблиц: {e}")


class AuthModel(BaseModel):
    username: str
    password: str


class FavoriteModel(BaseModel):
    user_id: str
    favorite_ids: List[int]


@router.post("/register")
async def register(data: AuthModel):
    ensure_tables_exist()
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT username FROM users WHERE username = %s;", (data.username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Пользователь уже существует")

        password_hash = hash_password(data.password)
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s);",
            (data.username, password_hash),
        )
        conn.commit()
        cur.close()
        conn.close()

        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")


@router.post("/login")
async def login(data: AuthModel):
    ensure_tables_exist()
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT username, password_hash FROM users WHERE username = %s;",
            (data.username,),
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not verify_password(data.password, user[1]):
            raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")

        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")


@router.get("/favorites")
async def get_favorites(user_id: str):
    ensure_tables_exist()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s;", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        return {"favorite_ids": row[0] if row and row[0] else []}
    except Exception:
        return {"favorite_ids": []}


@router.post("/favorites")
async def save_favorites(data: FavoriteModel):
    ensure_tables_exist()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO favorites (user_id, favorite_ids)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET favorite_ids = EXCLUDED.favorite_ids;
            """,
            (data.user_id, data.favorite_ids),
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")
