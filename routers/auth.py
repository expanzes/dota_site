import os, random, bcrypt, psycopg2, httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
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
                # Таблица пользователей
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
                cur.execute("CREATE TABLE IF NOT EXISTS favorites (user_id VARCHAR(10) PRIMARY KEY, favorite_ids INTEGER[]);")
                conn.commit()
    except Exception as e:
        print(f"CRITICAL DB ERROR: {e}")

@router.get("/login/steam")
async def steam_login(request: Request):
    if not STEAM_API_KEY:
        raise HTTPException(status_code=500, detail="STEAM_API_KEY не задан в настройках сервера")
    
    base_url = str(request.base_url).rstrip('/')
    # Убедись, что на Render в настройках URL сайта указан верно
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
        if not claimed_id: 
            return RedirectResponse("/")
        
        steam_id = claimed_id.split("/")[-1]

        async with httpx.AsyncClient() as client:
            # 1. Получаем данные из Steam
            res = await client.get(
                f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}",
                timeout=10.0
            )
            data = res.json()
            if not data.get("response") or not data["response"].get("players"):
                raise Exception("Steam API не вернул данные игрока")
            
            s_data = data["response"]["players"][0]
            
            # 2. Получаем ранг из OpenDota
            rank = 0
            try:
                od = await client.get(f"https://api.opendota.com/api/players/{steam_id}", timeout=5.0)
                if od.status_code == 200:
                    rank = od.json().get("rank_tier", 0)
            except: pass

        # 3. Работа с БД
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT site_id, username FROM users WHERE steam_id = %s", (steam_id,))
                user = cur.fetchone()
                
                if not user:
                    sid = generate_site_id()
                    username = s_data["personaname"]
                    # Если такой ник уже есть (редкий случай), добавим цифры
                    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                    if cur.fetchone():
                        username = f"{username}_{sid[:4]}"
                        
                    cur.execute("""
                        INSERT INTO users (site_id, username, steam_id, avatar_url, rank_tier)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (sid, username, steam_id, s_data["avatarfull"], rank))
                else:
                    sid, username = user[0], user[1]
                    cur.execute("UPDATE users SET avatar_url = %s, rank_tier = %s WHERE site_id = %s", 
                               (s_data["avatarfull"], rank, sid))
                conn.commit()

        # 4. Сохраняем в сессию
        request.session["user"] = {"site_id": sid, "username": username}
        return RedirectResponse("/profile")

    except Exception as e:
        print(f"STEAM CALLBACK ERROR: {e}")
        return HTMLResponse(content=f"<h1>Ошибка авторизации</h1><p>{str(e)}</p>")

@router.get("/me")
async def get_me(request: Request):
    sess = request.session.get("user")
    if not sess: return {"logged_in": False}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT site_id, username, avatar_url, rank_tier, invoker_high_score, is_premium, steam_id FROM users WHERE site_id = %s", (sess["site_id"],))
                u = cur.fetchone()
                if not u: return {"logged_in": False}
                return {
                    "logged_in": True, "site_id": u[0], "username": u[1], 
                    "avatar": u[2], "rank": u[3], "invoker_score": u[4], 
                    "is_premium": u[5], "steam_linked": bool(u[6])
                }
    except: return {"logged_in": False}

# (Остальные функции: register, login, save_score и т.д. остаются без изменений)
