import os, bcrypt, psycopg2
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing")
    return psycopg2.connect(DATABASE_URL)

def hash_password(pw: str):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, h: str):
    return bcrypt.checkpw(pw.encode(), h.encode())

def ensure_tables_exist():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Таблица пользователей
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        username VARCHAR(100) UNIQUE NOT NULL, 
                        password_hash VARCHAR(255) NOT NULL,
                        invoker_high_score INTEGER DEFAULT 0
                    );
                """)
                # Добавляем колонку рекорда, если её нет
                cur.execute("""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='invoker_high_score') THEN
                            ALTER TABLE users ADD COLUMN invoker_high_score INTEGER DEFAULT 0;
                        END IF;
                    END $$;
                """)
                # Таблица избранного
                cur.execute("CREATE TABLE IF NOT EXISTS favorites (user_id VARCHAR(100) PRIMARY KEY, favorite_ids INTEGER[]);")
                conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")

class AuthModel(BaseModel):
    username: str
    password: str

class FavoriteModel(BaseModel):
    user_id: str
    favorite_ids: List[int]

class ScoreModel(BaseModel):
    username: str
    score: int

@router.post("/register")
async def register(data: AuthModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (data.username,))
                if cur.fetchone():
                    raise HTTPException(400, "Пользователь существует")
                cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (data.username, hash_password(data.password)))
                conn.commit()
        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/login")
async def login(data: AuthModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (data.username,))
                row = cur.fetchone()
                if not row or not verify_password(data.password, row[0]):
                    raise HTTPException(400, "Ошибка входа")
        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/favorites")
async def get_favorites(user_id: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s", (user_id,))
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
                    INSERT INTO favorites (user_id, favorite_ids) 
                    VALUES (%s, %s) 
                    ON CONFLICT (user_id) 
                    DO UPDATE SET favorite_ids = EXCLUDED.favorite_ids
                """, (data.user_id, data.favorite_ids))
                conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/save-invoker-score")
async def save_score(data: ScoreModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET invoker_high_score = GREATEST(invoker_high_score, %s) 
                    WHERE username = %s
                """, (data.score, data.username))
                conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/user-stats")
async def get_stats(username: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT invoker_high_score FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
        return {"high_score": row[0] if row else 0}
    except Exception:
        return {"high_score": 0}
