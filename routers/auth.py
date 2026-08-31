import os, random, bcrypt, psycopg2, httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def generate_site_id():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def hash_password(pw: str): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def verify_password(pw: str, h: str): return bcrypt.checkpw(pw.encode(), h.encode())

def ensure_tables_exist():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        site_id VARCHAR(10) PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255),
                        steam_id VARCHAR(50) UNIQUE,
                        avatar_url TEXT,
                        rank_tier INTEGER DEFAULT 0,
                        invoker_high_score INTEGER DEFAULT 0,
                        is_premium BOOLEAN DEFAULT FALSE
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS favorites (
                        user_id VARCHAR(10) PRIMARY KEY REFERENCES users(site_id),
                        favorite_ids INTEGER[]
                    );
                """)
                conn.commit()
    except Exception as e: print(f"DB Error: {e}")

async def get_favorites_db(user_id: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
                return {"favorite_ids": row[0] if row and row[0] else []}
    except: return {"favorite_ids": []}

class AuthModel(BaseModel):
    username: str
    password: str

class FavoriteModel(BaseModel):
    user_id: str
    favorite_ids: List[int]

class UpdateUsernameModel(BaseModel):
    site_id: str
    new_username: str

# --- РЕГИСТРАЦИЯ (С ФИКСОМ СЕССИИ) ---
@router.post("/register")
async def register(data: AuthModel, request: Request):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (data.username,))
                if cur.fetchone(): raise HTTPException(400, "Никнейм занят")
                sid = generate_site_id()
                cur.execute("INSERT INTO users (site_id, username, password_hash) VALUES (%s, %s, %s)", 
                           (sid, data.username, hash_password(data.password)))
                conn.commit()
                # УСТАНАВЛИВАЕМ СЕССИЮ
                request.session["user"] = {"site_id": sid, "username": data.username}
                return {"site_id": sid, "username": data.username}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(500, str(e))

# --- ЛОГИН (С ФИКСОМ СЕССИИ) ---
@router.post("/login")
async def login(data: AuthModel, request: Request):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT site_id, username, password_hash FROM users WHERE username = %s", (data.username,))
            row = cur.fetchone()
            if not row or not row[2] or not verify_password(data.password, row[2]):
                raise HTTPException(400, "Неверный логин или пароль")
            # УСТАНАВЛИВАЕМ СЕССИЮ
            request.session["user"] = {"site_id": row[0], "username": row[1]}
            return {"site_id": row[0], "username": row[1]}

@router.get("/login/steam")
async def steam_login(request: Request):
    base_url = str(request.base_url).rstrip('/')
    return_to = f"{base_url}/api/auth/steam/callback"
    url = (f"https://steamcommunity.com/openid/login?openid.ns=http://specs.openid.net/auth/2.0&"
           f"openid.mode=checkid_setup&openid.return_to={return_to}&openid.realm={base_url}&"
           f"openid.identity=http://specs.openid.net/auth/2.0/identifier_select&"
           f"openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select")
    return RedirectResponse(url)

@router.get("/auth/steam/callback")
async def steam_callback(request: Request):
    try:
        claimed_id = request.query_params.get("openid.claimed_id")
        if not claimed_id: return RedirectResponse("/")
        steam_id = claimed_id.split("/")[-1]
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}", timeout=10.0)
            s_data = res.json()["response"]["players"][0]
            od = await client.get(f"https://api.opendota.com/api/players/{steam_id}", timeout=5.0)
            rank = od.json().get("rank_tier", 0) if od.status_code == 200 else 0
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT site_id, username FROM users WHERE steam_id = %s", (steam_id,))
                user = cur.fetchone()
                if not user:
                    sid = generate_site_id()
                    username = s_data["personaname"]
                    cur.execute("INSERT INTO users (site_id, username, steam_id, avatar_url, rank_tier) VALUES (%s, %s, %s, %s, %s)", 
                               (sid, username, steam_id, s_data["avatarfull"], rank))
                else:
                    sid, username = user[0], user[1]
                    cur.execute("UPDATE users SET avatar_url = %s, rank_tier = %s WHERE site_id = %s", (s_data["avatarfull"], rank, sid))
                conn.commit()
        request.session["user"] = {"site_id": sid, "username": username}
        return RedirectResponse("/profile")
    except Exception as e: return HTMLResponse(content=f"<h1>Ошибка</h1><p>{str(e)}</p>")

@router.get("/me")
async def get_me(request: Request):
    sess = request.session.get("user")
    if not sess: return {"logged_in": False}
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT site_id, username, avatar_url, rank_tier, invoker_high_score, is_premium, steam_id FROM users WHERE site_id = %s", (sess["site_id"],))
            u = cur.fetchone()
            if not u: return {"logged_in": False}
            return {"logged_in": True, "site_id": u[0], "username": u[1], "avatar": u[2], "rank": u[3], "invoker_score": u[4], "is_premium": u[5], "steam_linked": bool(u[6])}

@router.get("/favorites")
async def get_favs_api(user_id: str): return await get_favorites_db(user_id)

@router.post("/favorites")
async def save_favorites(data: FavoriteModel):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO favorites (user_id, favorite_ids) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET favorite_ids = EXCLUDED.favorite_ids", (data.user_id, data.favorite_ids))
            conn.commit()
    return {"status": "ok"}

@router.post("/update-username")
async def update_username(data: UpdateUsernameModel):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET username = %s WHERE site_id = %s", (data.new_username, data.site_id))
            conn.commit()
    return {"status": "ok"}

@router.get("/user-stats")
async def get_stats(username: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT invoker_high_score FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
    return {"high_score": row[0] if row else 0}

@router.post("/save-invoker-score")
async def save_score(data: dict):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET invoker_high_score = GREATEST(invoker_high_score, %s) WHERE username = %s", (data['score'], data['username']))
            conn.commit()
    return {"status": "ok"}
