import os
import psycopg2
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("Переменная окружения DATABASE_URL не задана")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    if not DATABASE_URL:
        return
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS favorites (
                user_id VARCHAR(100) PRIMARY KEY,
                heroes TEXT[]
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")

# Создаем таблицы при запуске модуля
init_db()

class AuthModel(BaseModel):
    username: str
    password: str

class FavoriteModel(BaseModel):
    user_id: str
    heroes: List[str]

@router.post("/register")
async def register(data: AuthModel):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT username FROM users WHERE username = %s;", (data.username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s);", (data.username, data.password))
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
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT username, password FROM users WHERE username = %s;", (data.username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or user[1] != data.password:
            raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")
        
        return {"user_id": f"user_{data.username}", "username": data.username}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")

@router.get("/favorites/{user_id}")
async def get_favorites(user_id: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT heroes FROM favorites WHERE user_id = %s;", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        return row[0] if row and row[0] else []
    except Exception:
        return []

@router.post("/favorites")
async def save_favorites(data: FavoriteModel):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO favorites (user_id, heroes)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET heroes = EXCLUDED.heroes;
        """, (data.user_id, data.heroes))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")
