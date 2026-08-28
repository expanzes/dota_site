import os
import sqlite3
import hashlib
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI(title="Dota 2 Helper")

# Инициализация базы данных SQLite
DB_NAME = "dota_helper.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Таблица любимых героев (пул)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL,
            hero_name TEXT NOT NULL,
            PRIMARY KEY (user_id, hero_name),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists("static/index.html"):
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dota 2 Helper API Running</h1>"

@app.get("/site", response_class=HTMLResponse)
async def read_site():
    return await read_root()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

ROLES_DB = {
    "pos1": {"antimage", "spectre", "phantom_assassin", "juggernaut", "faceless_void", "slark", "sven", "bloodseeker", "gyrocopter", "lifestealer", "luna", "medusa", "monkey_king", "morphling", "naga_siren", "sniper", "terrorblade", "troll_warlord", "ursa", "wraith_king", "weaver", "clinkz", "drow_ranger"},
    "pos2": {"storm_spirit", "ember_spirit", "void_spirit", "invoker", "shadow_fiend", "puck", "queen_of_pain", "tinker", "lina", "sniper", "templar_assassin", "dragon_knight", "death_prophet", "leshrac", "kunkka", "meepo", "necrophos", "pudge", "tiny", "windranger", "zeus"},
    "pos3": {"mars", "tidehunter", "axe", "centaur", "bristleback", "slardar", "underlord", "beastmaster", "brewmaster", "doom", "dark_seer", "enigma", "legion_commander", "magnus", "night_stalker", "sand_king", "timbersaw", "viper", "visage"},
    "pos4": {"rubick", "mirana", "lion", "shadow_shaman", "earth_spirit", "tusk", "clockwerk", "bounty_hunter", "hoodwink", "nyx_assassin", "phoenix", "pudge", "skywrath_mage", "snapfire", "spirit_breaker", "techies", "tiny", "ancient_apparition"},
    "pos5": {"crystal_maiden", "jakiro", "witch_doctor", "ogre_magi", "dazzle", "disruptor", "lich", "oracle", "shadow_demon", "silencer", "treant", "warlock", "bane", "chen", "grimstroke", "io", "keeper_of_the_light", "omniknight", "undying"}
}

def get_opendota_heroes():
    try:
        r = requests.get("https://api.opendota.com/api/heroes", timeout=10)
        if r.status_code == 200:
            return {h["id"]: {"name": h["localized_name"], "slug": h["name"].replace("npc_dota_hero_", "")} for h in r.json()}
    except Exception:
        pass
    return {}

# --- ЭНДПОИНТЫ АВТОРИЗАЦИИ И ПУЛА ГЕРОЕВ ---

class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/api/register")
def register(req: AuthRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    pwd_hash = hash_password(req.password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (req.username, pwd_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"status": "ok", "user_id": user_id, "username": req.username}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

@app.post("/api/login")
def login(req: AuthRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    pwd_hash = hash_password(req.password)
    cursor.execute("SELECT id, username FROM users WHERE username = ? AND password_hash = ?", (req.username, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"status": "ok", "user_id": user[0], "username": user[1]}
    raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")

class FavoritesRequest(BaseModel):
    user_id: int
    heroes: List[str]

@app.get("/api/favorites/{user_id}")
def get_favorites(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT hero_name FROM favorites WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

@app.post("/api/favorites")
def save_favorites(req: FavoritesRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE user_id = ?", (req.user_id,))
    for hero in req.heroes:
        cursor.execute("INSERT INTO favorites (user_id, hero_name) VALUES (?, ?)", (req.user_id, hero))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/heroes")
def api_heroes():
    heroes = get_opendota_heroes()
    names = [h["name"] for h in heroes.values()]
    return sorted(names)

# --- ЛОГИКА ДРАФТА С УЧЕТОМ ПУЛА ГЕРОЕВ ---

def get_role_data(role_key: str, candidate_stats: dict, heroes_map: dict, user_favs: set):
    valid_heroes = ROLES_DB.get(role_key, set())
    role_candidates = []
    all_candidates = []

    for cid, data in candidate_stats.items():
        hero_info = heroes_map.get(cid)
        if not hero_info or data.get("games", 0) < 1:
            continue

        wr = (data["wins"] / data["games"]) * 100 if data["games"] > 0 else 0
        img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_info['slug']}.png"
        item = {
            "name": hero_info["name"],
            "winrate": round(wr, 1),
            "games": data["games"],
            "img": img_url,
            "is_fav": hero_info["name"].lower() in user_favs
        }

        all_candidates.append(item)
        if hero_info["slug"] in valid_heroes or hero_info["name"].lower().replace(" ", "_") in valid_heroes:
            role_candidates.append(item)

    final_list = role_candidates if role_candidates else all_candidates
    if not final_list:
        return None

    by_winrate = sorted(final_list, key=lambda x: x["winrate"], reverse=True)
    by_games = sorted(final_list, key=lambda x: x["games"], reverse=True)

    top_wr = by_winrate[0]
    top_gm = by_games[0]

    # Ищем лучший контрпик из пула авторизованного пользователя
    fav_candidates = [h for h in by_winrate if h["is_fav"]]
    top_fav = fav_candidates[0] if fav_candidates else None

    # Исключаем главных героев из блока "Другие варианты"
    excluded_names = {top_wr["name"], top_gm["name"]}
    if top_fav:
        excluded_names.add(top_fav["name"])

    others = [h for h in by_winrate if h["name"] not in excluded_names][:3]

    return {
        "top_favorite": top_fav,
        "top_winrate": top_wr,
        "top_games": top_gm,
        "others": others,
    }

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[int] = None

@app.post("/api/analyze")
def analyze_draft(req: DraftRequest):
    heroes_map = get_opendota_heroes()
    name_to_id = {info["name"].lower(): hid for hid, info in heroes_map.items()}

    # Если передан user_id, загружаем пул героя данного пользователя
    user_favs = set()
    if req.user_id:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT hero_name FROM favorites WHERE user_id = ?", (req.user_id,))
        rows = cursor.fetchall()
        conn.close()
        user_favs = {r[0].lower() for r in rows}

    enemy_ids = []
    for e in req.enemy_team:
        clean_name = e.split('/')[0].strip().lower()
        if clean_name in name_to_id:
            enemy_ids.append(name_to_id[clean_name])

    candidate_stats = {}
    if enemy_ids:
        for eid in enemy_ids:
            try:
                r = requests.get(f"https://api.opendota.com/api/heroes/{eid}/matchups", timeout=5)
                if r.status_code == 200:
                    for item in r.json():
                        cid = item["hero_id"]
                        if cid not in candidate_stats:
                            candidate_stats[cid] = {"wins": 0, "games": 0}
                        candidate_stats[cid]["games"] += item["games_played"]
                        candidate_stats[cid]["wins"] += item["wins"]
            except Exception:
                pass

    roles_display = [
        ("Поз 1 (Керри)", "pos1"),
        ("Поз 2 (Мид)", "pos2"),
        ("Поз 3 (Тройка)", "pos3"),
        ("Поз 4 (Четверка)", "pos4"),
        ("Поз 5 (Пятерка)", "pos5"),
    ]

    results = []
    for role_name, role_key in roles_display:
        if not req.my_team.get(role_key):
            rdata = get_role_data(role_key, candidate_stats, heroes_map, user_favs)
            results.append({"role": role_name, "data": rdata})

    return {"status": "ok", "results": results}

@app.get("/api/news")
def get_news():
    try:
        r = requests.get("https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid=570&count=5&maxlength=300&format=json", timeout=5)
        if r.status_code == 200:
            items = r.json().get("appnews", {}).get("newsitems", [])
            news_list = []
            import datetime
            for item in items:
                date_str = datetime.datetime.fromtimestamp(item.get("date", 0)).strftime("%d.%m.%Y")
                news_list.append({
                    "title": item.get("title", ""),
                    "contents": item.get("contents", ""),
                    "url": item.get("url", "#"),
                    "author": item.get("author", "Valve"),
                    "date": date_str
                })
            return news_list
    except Exception:
        pass
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
