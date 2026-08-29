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
        "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s;",
        (table, column),
    )
    return cur.fetchone() is not None

def ensure_tables_exist():
    """Создаёт таблицы и мигрирует схему. Вызывается один раз при старте."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Таблица пользователей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255)
                    );
                """)
                
                # Миграция паролей (если старая колонка 'password' существует)
                if _column_exists(cur, "users", "password") and not _column_exists(cur, "users", "password_hash"):
                    cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);")
                    cur.execute("SELECT id, password FROM users WHERE password IS NOT NULL;")
                    for user_id, plain in cur.fetchall():
                        cur.execute("UPDATE users SET password_hash = %s WHERE id = %s;", (hash_password(plain), user_id))
                    cur.execute("ALTER TABLE users DROP COLUMN password;")
                    cur.execute("ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;")

                # Таблица избранного
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS favorites (
                        user_id VARCHAR(100) PRIMARY KEY,
                        favorite_ids INTEGER[]
                    );
                """)
                conn.commit()
        print("База данных проверена и готова к работе.")
    except Exception as e:
        print(f"Ошибка миграции таблиц: {e}")

class AuthModel(BaseModel):
    username: str
    password: str

class FavoriteModel(BaseModel):
    user_id: str
    favorite_ids: List[int]

@router.post("/register")
async def register(data: AuthModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s;", (data.username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Пользователь уже существует")
                
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s);",
                    (data.username, hash_password(data.password)),
                )
                conn.commit()
        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(data: AuthModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE username = %s;", (data.username,))
                row = cur.fetchone()
                if not row or not verify_password(data.password, row[0]):
                    raise HTTPException(status_code=400, detail="Неверное имя или пароль")
        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/favorites")
async def get_favorites(user_id: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s;", (user_id,))
                row = cur.fetchone()
        return {"favorite_ids": row[0] if row and row[0] else []}
    except Exception:
        return {"favorite_ids": []}

@router.post("/favorites")
async def save_favorites(data: FavoriteModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO favorites (user_id, favorite_ids) VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET favorite_ids = EXCLUDED.favorite_ids;
                """, (data.user_id, data.favorite_ids))
                conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
