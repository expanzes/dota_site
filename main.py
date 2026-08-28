import os
import sqlite3
import hashlib
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional

# Подключение PostgreSQL для Render / Neon.tech
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    import psycopg2
    # В некоторых сервисах URL начинается с postgres://, заменяем на postgresql:// для psycopg2
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app = FastAPI(title="Dota 2 Helper")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_root():
    possible_paths = [
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(BASE_DIR, "index.html"),
        "static/index.html",
        "index.html"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)

    files_in_base = os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else []
    files_in_static = os.listdir(STATIC_DIR) if os.path.exists(STATIC_DIR) else "Папка static отсутствует"
    
    debug_html = f"""
    <html>
        <body style="font-family: sans-serif; background: #111; color: #fff; padding: 20px;">
            <h1 style="color: #ff4655;">Сервер запущен, но index.html не найден!</h1>
            <p><b>Текущая директория (BASE_DIR):</b> {BASE_DIR}</p>
            <p><b>Файлы в корне проекта:</b> {files_in_base}</p>
            <p><b>Файлы в папке static:</b> {files_in_static}</p>
        </body>
    </html>
    """
    return HTMLResponse(content=debug_html, status_code=200)

# --- Работа с БД (PostgreSQL на Render / SQLite локально) ---
def get_db():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        return conn, "pg"
    else:
        DB_NAME = os.path.join(BASE_DIR, "dota_helper.db")
        conn = sqlite3.connect(DB_NAME)
        return conn, "sqlite"

def init_db():
    conn, db_type = get_db()
    cursor = conn.cursor()
    if db_type == "pg":
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                hero_name TEXT NOT NULL,
                PRIMARY KEY (user_id, hero_name),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
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

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

ROLES_DB = {
    "pos1": {"antimage", "spectre", "phantom_assassin", "juggernaut", "faceless_void", "slark", "sven", "bloodseeker", "gyrocopter", "lifestealer", "luna", "medusa", "monkey_king", "morphling", "naga_siren", "sniper", "terrorblade", "troll_warlord", "ursa", "wraith_king", "weaver", "clinkz", "drow_ranger", "riki", "void_spirit"},
    "pos2": {"storm_spirit", "ember_spirit", "void_spirit", "invoker", "shadow_fiend", "puck", "queen_of_pain", "tinker", "lina", "sniper", "templar_assassin", "dragon_knight", "death_prophet", "leshrac", "kunkka", "meepo", "necrophos", "pudge", "tiny", "windranger", "zeus", "earth_spirit", "pangolier"},
    "pos3": {"mars", "tidehunter", "axe", "centaur", "bristleback", "slardar", "underlord", "beastmaster", "brewmaster", "doom", "dark_seer", "enigma", "legion_commander", "magnus", "night_stalker", "sand_king", "timbersaw", "viper", "visage", "dawnbreaker", "primal_beast"},
    "pos4": {"rubick", "mirana", "lion", "shadow_shaman", "earth_spirit", "tusk", "clockwerk", "bounty_hunter", "hoodwink", "nyx_assassin", "phoenix", "pudge", "skywrath_mage", "snapfire", "spirit_breaker", "techies", "tiny", "ancient_apparition", "marci"},
    "pos5": {"crystal_maiden", "jakiro", "witch_doctor", "ogre_magi", "dazzle", "disruptor", "lich", "oracle", "shadow_demon", "silencer", "treant", "warlock", "bane", "chen", "grimstroke", "io", "keeper_of_the_light", "omniknight", "undying", "abaddon"}
}

HERO_ALIASES = {
    "сф": "shadow fiend", "sf": "shadow fiend",
    "ам": "anti-mage", "am": "anti-mage",
    "па": "phantom assassin", "pa": "phantom assassin",
    "морф": "morphling", "morph": "morphling",
    "бара": "spirit breaker", "sb": "spirit breaker",
    "аппарат": "ancient apparition", "aa": "ancient apparition",
    "вр": "windranger", "wr": "windranger",
    "дк": "dragon knight", "dk": "dragon knight",
    "тб": "terrorblade", "tb": "terrorblade",
    "пб": "primal beast", "pb": "primal beast",
    "мк": "monkey king", "mk": "monkey king",
    "квопа": "queen of pain", "qop": "queen of pain",
    "та": "templar assassin", "ta": "templar assassin",
    "воид": "faceless void", "fv": "faceless void",
    "шторм": "storm spirit", "шторм спирит": "storm spirit",
    "земля": "earth spirit", "земля спирит": "earth spirit",
    "эмбер": "ember spirit", "эмбер спирит": "ember spirit"
}

def get_opendota_heroes():
    try:
        r = requests.get("https://api.opendota.com/api/heroes", timeout=10)
        if r.status_code == 200:
            res = {}
            for h in r.json():
                slug = h["name"].replace("npc_dota_hero_", "")
                res[h["id"]] = {
                    "id": h["id"],
                    "name": h["localized_name"],
                    "slug": slug,
                    "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{slug}.png"
                }
            return res
    except Exception:
        pass
    return {}

class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/api/register")
def register(req: AuthRequest):
    conn, db_type = get_db()
    cursor = conn.cursor()
    pwd_hash = hash_password(req.password)
    try:
        if db_type == "pg":
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id", (req.username, pwd_hash))
            user_id = cursor.fetchone()[0]
        else:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (req.username, pwd_hash))
            user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"status": "ok", "user_id": user_id, "username": req.username}
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

@app.post("/api/login")
def login(req: AuthRequest):
    conn, db_type = get_db()
    cursor = conn.cursor()
    pwd_hash = hash_password(req.password)
    placeholder = "%s" if db_type == "pg" else "?"
    cursor.execute(f"SELECT id, username FROM users WHERE username = {placeholder} AND password_hash = {placeholder}", (req.username, pwd_hash))
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
    conn, db_type = get_db()
    cursor = conn.cursor()
    placeholder = "%s" if db_type == "pg" else "?"
    cursor.execute(f"SELECT hero_name FROM favorites WHERE user_id = {placeholder}", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

@app.post("/api/favorites")
def save_favorites(req: FavoritesRequest):
    conn, db_type = get_db()
    cursor = conn.cursor()
    placeholder = "%s" if db_type == "pg" else "?"
    cursor.execute(f"DELETE FROM favorites WHERE user_id = {placeholder}", (req.user_id,))
    for hero in req.heroes:
        cursor.execute(f"INSERT INTO favorites (user_id, hero_name) VALUES ({placeholder}, {placeholder})", (req.user_id, hero))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/heroes")
def api_heroes():
    heroes = get_opendota_heroes()
    out = []
    for h in heroes.values():
        out.append({
            "id": h["id"],
            "name": h["name"],
            "slug": h["slug"],
            "img": h["img"]
        })
    return sorted(out, key=lambda x: x["name"])

def get_role_data(role_key: str, candidate_stats: dict, heroes_map: dict, user_favs: set, banned_hero_ids: set):
    valid_heroes = ROLES_DB.get(role_key, set())
    role_candidates = []
    all_candidates = []

    for cid, data in candidate_stats.items():
        if cid in banned_hero_ids:
            continue

        hero_info = heroes_map.get(cid)
        if not hero_info or data.get("games", 0) < 10:
            continue

        cand_wins = data["cand_wins"]
        games = data["games"]
        wr = (cand_wins / games) * 100 if games > 0 else 0
        has_hard_counter = data.get("has_hard_counter", False)

        item = {
            "name": hero_info["name"],
            "winrate": round(wr, 1),
            "games": games,
            "img": hero_info["img"],
            "is_fav": hero_info["name"].lower() in user_favs,
            "has_hard_counter": has_hard_counter
        }

        all_candidates.append(item)
        if hero_info["slug"] in valid_heroes or hero_info["name"].lower().replace(" ", "_") in valid_heroes:
            role_candidates.append(item)

    pool = role_candidates if role_candidates else all_candidates
    if not pool:
        return None

    safe_pool = [h for h in pool if not h["has_hard_counter"]]
    eval_pool = safe_pool if safe_pool else pool

    by_winrate = sorted(eval_pool, key=lambda x: x["winrate"], reverse=True)
    by_games = sorted(eval_pool, key=lambda x: x["games"], reverse=True)

    top_wr = by_winrate[0]
    top_gm = by_games[0]

    fav_candidates = [h for h in by_winrate if h["is_fav"] and not h["has_hard_counter"] and h["winrate"] >= 46.0]
    top_fav = fav_candidates[0] if fav_candidates else None

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
    
    name_to_id = {}
    for hid, info in heroes_map.items():
        name_to_id[info["name"].lower()] = hid
        name_to_id[info["slug"].lower()] = hid

    banned_hero_ids = set()

    for hname in list(req.my_team.values()) + req.enemy_team:
        clean = hname.strip().lower()
        if clean in HERO_ALIASES:
            clean = HERO_ALIASES[clean]
        if clean in name_to_id:
            banned_hero_ids.add(name_to_id[clean])

    enemy_ids = []
    for e in req.enemy_team:
        clean = e.strip().lower()
        if clean in HERO_ALIASES:
            clean = HERO_ALIASES[clean]
        if clean in name_to_id:
            enemy_ids.append(name_to_id[clean])

    user_favs = set()
    if req.user_id:
        conn, db_type = get_db()
        cursor = conn.cursor()
        placeholder = "%s" if db_type == "pg" else "?"
        cursor.execute(f"SELECT hero_name FROM favorites WHERE user_id = {placeholder}", (req.user_id,))
        rows = cursor.fetchall()
        conn.close()
        user_favs = {r[0].lower() for r in rows}

    candidate_stats = {}

    if enemy_ids:
        for eid in enemy_ids:
            try:
                r = requests.get(f"https://api.opendota.com/api/heroes/{eid}/matchups", timeout=5)
                if r.status_code == 200:
                    for item in r.json():
                        cid = item["hero_id"]
                        games = item["games_played"]
                        enemy_wins = item["wins"]
                        
                        cand_wins_vs_enemy = games - enemy_wins
                        single_matchup_wr = (cand_wins_vs_enemy / games) * 100 if games > 0 else 50.0

                        if cid not in candidate_stats:
                            candidate_stats[cid] = {"cand_wins": 0, "games": 0, "has_hard_counter": False}

                        candidate_stats[cid]["games"] += games
                        candidate_stats[cid]["cand_wins"] += cand_wins_vs_enemy

                        if single_matchup_wr < 42.0:
                            candidate_stats[cid]["has_hard_counter"] = True
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
            rdata = get_role_data(role_key, candidate_stats, heroes_map, user_favs, banned_hero_ids)
            results.append({"role": role_name, "data": rdata})

    return {"status": "ok", "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
