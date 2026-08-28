from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Временное хранилище (в памяти)
USERS_DB = {}
FAVORITES_DB = {}

class AuthModel(BaseModel):
    username: str
    password: str

class FavoriteModel(BaseModel):
    user_id: str
    heroes: List[str]

@router.post("/register")
async def register(data: AuthModel):
    if data.username in USERS_DB:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    USERS_DB[data.username] = data.password
    user_id = f"user_{data.username}"
    return {"user_id": user_id, "username": data.username}

@router.post("/login")
async def login(data: AuthModel):
    if data.username not in USERS_DB or USERS_DB[data.username] != data.password:
        raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")
    user_id = f"user_{data.username}"
    return {"user_id": user_id, "username": data.username}

@router.get("/favorites/{user_id}")
async def get_favorites(user_id: str):
    return FAVORITES_DB.get(user_id, [])

@router.post("/favorites")
async def save_favorites(data: FavoriteModel):
    FAVORITES_DB[data.user_id] = data.heroes
    return {"status": "ok"}
