import os, random, bcrypt, psycopg2, httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# ТВОЙ НОВЫЙ ДОМЕН
MY_DOMAIN = "dotahelper.ru"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def generate_site_id():
    """Генерирует уникальный 10-значный ID"""
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def hash_password(pw: str): 
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, h: str): 
    return bcrypt.checkpw(pw.encode(), h.encode())

def to_account_id(steam64):
    """Конвертация SteamID64 в Account ID для OpenDota"""
    try: return int(steam64) - 76561197960265728
    except: return steam64

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
    except Exception as e: 
        print(f"DB Error: {e}")

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

class ScoreModel(BaseModel):
    username: str
    score: int

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "ok"}

@router.get("/login/steam")
async def steam_login(request: Request):
    return_to = f"https://{MY_DOMAIN}/api/auth/steam/callback"
    realm = f"https://{MY_DOMAIN}"
    
    url = (f"https://steamcommunity.com/openid/login?openid.ns=http://specs.openid.net/auth/2.0&"
           f"openid.mode=checkid_setup&openid.return_to={return_to}&openid.realm={realm}&"
           f"openid.identity=http://specs.openid.net/auth/2.0/identifier_select&"
           f"openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select")
    return RedirectResponse(url)

@router.get("/auth/steam/callback")
async def steam_callback(request: Request):
    try:
        claimed_id = request.query_params.get("openid.claimed_id")
        if not claimed_id: return RedirectResponse("/")
        steam_id = claimed_id.split("/")[-1]
        account_id = to_account_id(steam_id)

        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}", timeout=15.0)
            s_data = res.json()["response"]["players"][0]
            od = await client.get(f"https://api.opendota.com/api/players/{account_id}", timeout=5.0)
            rank = od.json().get("rank_tier", 0) if od.status_code == 200 else 0

        current_session = request.session.get("user")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT site_id, username FROM users WHERE steam_id = %s", (steam_id,))
                existing = cur.fetchone()

                if current_session:
                    sid = current_session["site_id"]
                    cur.execute("UPDATE users SET steam_id = %s, avatar_url = %s, rank_tier = %s WHERE site_id = %s", 
                               (steam_id, s_data["avatarfull"], rank, sid))
                    username = current_session["username"]
                elif existing:
                    sid, username = existing[0], existing[1]
                    cur.execute("UPDATE users SET avatar_url = %s, rank_tier = %s WHERE site_id = %s", 
                               (s_data["avatarfull"], rank, sid))
                else:
                    sid = generate_site_id()
                    username = s_data["personaname"]
                    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                    if cur.fetchone(): username = f"{username}_{sid[:4]}"
                    cur.execute("INSERT INTO users (site_id, username, steam_id, avatar_url, rank_tier) VALUES (%s, %s, %s, %s, %s)", 
                               (sid, username, steam_id, s_data["avatarfull"], rank))
                conn.commit()

        request.session["user"] = {"site_id": sid, "username": username}
        return RedirectResponse("/profile")
    except Exception as e: 
        return HTMLResponse(content=f"<h1>Ошибка авторизации</h1><p>{str(e)}</p>")

@router.get("/me")
async def get_me(request: Request):
    sess = request.session.get("user")
    if not sess: return {"logged_in": False}
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT site_id, username, avatar_url, rank_tier, invoker_high_score, is_premium, steam_id FROM users WHERE site_id = %s", (sess["site_id"],))
            u = cur.fetchone()
            if not u: return {"logged_in": False}
            
            rank = u[3]
            if rank == 0 and u[6]:
                try:
                    acc_id = to_account_id(u[6])
                    async with httpx.AsyncClient() as client:
                        od = await client.get(f"https://api.opendota.com/api/players/{acc_id}", timeout=2.0)
                        if od.status_code == 200:
                            new_rank = od.json().get("rank_tier", 0)
                            if new_rank:
                                cur.execute("UPDATE users SET rank_tier = %s WHERE site_id = %s", (new_rank, u[0]))
                                conn.commit()
                                rank = new_rank
                except: pass

            return {
                "logged_in": True, "site_id": u[0], "username": u[1], 
                "avatar": u[2], "rank": rank, "invoker_score": u[4], 
                "is_premium": u[5], "steam_linked": bool(u[6])
            }

@router.post("/register")
async def register(data: AuthModel, request: Request):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (data.username,))
                if cur.fetchone(): raise HTTPException(status_code=400, detail="Никнейм занят")
                sid = generate_site_id()
                cur.execute("INSERT INTO users (site_id, username, password_hash) VALUES (%s, %s, %s)", 
                           (sid, data.username, hash_password(data.password)))
                conn.commit()
                request.session["user"] = {"site_id": sid, "username": data.username}
                return {"site_id": sid, "username": data.username}
    except Exception as e: raise HTTPException(500, str(e))

@router.post("/login")
async def login(data: AuthModel, request: Request):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT site_id, username, password_hash FROM users WHERE username = %s", (data.username,))
            row = cur.fetchone()
            if not row or not row[2] or not verify_password(data.password, row[2]):
                raise HTTPException(400, "Неверные данные")
            request.session["user"] = {"site_id": row[0], "username": row[1]}
            return {"site_id": row[0], "username": row[1]}

@router.post("/update-username")
async def update_username(data: UpdateUsernameModel):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET username = %s WHERE site_id = %s", (data.new_username, data.site_id))
                conn.commit()
        return {"status": "ok"}
    except: raise HTTPException(400, "Никнейм занят")

@router.get("/user-stats")
async def get_stats(username: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT invoker_high_score FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
    return {"high_score": row[0] if row else 0}

@router.post("/save-invoker-score")
async def save_score(data: ScoreModel):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET invoker_high_score = GREATEST(invoker_high_score, %s) WHERE username = %s", (data.score, data.username))
            conn.commit()
    return {"status": "ok"}

@router.get("/favorites")
async def get_favs_api(user_id: str): return await get_favorites_db(user_id)

@router.post("/favorites")
async def save_favorites(data: FavoriteModel):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO favorites (user_id, favorite_ids) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET favorite_ids = EXCLUDED.favorite_ids", (data.user_id, data.favorite_ids))
            conn.commit()
    return {"status": "ok"}

# --- НОВЫЙ ЭНДПОИНТ ДЛЯ ПОСЛЕДНИХ МАТЧЕЙ ---
@router.get("/recent-matches")
async def get_recent_matches(request: Request):
    sess = request.session.get("user")
    if not sess: return []
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT steam_id FROM users WHERE site_id = %s", (sess["site_id"],))
            u = cur.fetchone()
            if not u or not u[0]: return []
            steam_id = u[0]
            
    account_id = to_account_id(steam_id)
    
    async with httpx.AsyncClient() as client:
        try:
            # Получаем героев для красивых картинок
            heroes_res = await client.get("https://api.opendota.com/api/heroes", timeout=5.0)
            heroes_dict = {h["id"]: h for h in heroes_res.json()} if heroes_res.status_code == 200 else {}
            
            # Получаем матчи
            res = await client.get(f"https://api.opendota.com/api/players/{account_id}/recentMatches", timeout=10.0)
            if res.status_code != 200: return []
            data = res.json()[:10]
            
            matches = []
            for m in data:
                hero_data = heroes_dict.get(m.get("hero_id"))
                hero_img = ""
                if hero_data:
                    img_name = hero_data["name"].replace("npc_dota_hero_", "")
                    hero_img = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{img_name}.png"
                
                duration = m.get("duration", 0)
                gpm = m.get("gold_per_min", 0)
                # Нетворс = GPM * (Минуты)
                net_worth = int(gpm * (duration / 60))
                
                # Логика победы (Radiant < 128, Dire >= 128)
                is_radiant = m.get("player_slot", 0) < 128
                is_win = (m.get("radiant_win") and is_radiant) or (not m.get("radiant_win") and not is_radiant)
                
                matches.append({
                    "match_id": m.get("match_id"),
                    "hero_img": hero_img,
                    "kills": m.get("kills", 0),
                    "deaths": m.get("deaths", 0),
                    "assists": m.get("assists", 0),
                    "net_worth": net_worth,
                    "duration": duration,
                    "is_win": is_win
                })
            return matches
        except:
            return []
