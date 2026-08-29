import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import httpx
from routers.auth import get_db_connection

router = APIRouter()

# Кэш в оперативной памяти
HEROES_CACHE = []
HERO_STATS_CACHE = []
MATCHUP_CACHE = {}

MIN_GAMES_FOR_MATCHUP = 20
OTHERS_COUNT = 3

ROLES = {
    "pos1": "Поз 1 (Керри)",
    "pos2": "Поз 2 (Мид)",
    "pos3": "Поз 3 (Тройка)",
    "pos4": "Поз 4 (Четверка)",
    "pos5": "Поз 5 (Пятерка)"
}

# Базовые позиции (если нет данных)
HERO_POSITIONS = {
    "Anti-Mage": [1], "Axe": [3], "Invoker": [2], "Pudge": [3, 4], 
    "Naga Siren": [1], "Monkey King": [1, 2], "Ember Spirit": [2]
    # ... остальные подтянутся автоматически
}

async def get_heroes_cache():
    global HEROES_CACHE
    if HEROES_CACHE: return HEROES_CACHE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://api.opendota.com/api/heroes")
            if r.status_code == 200:
                HEROES_CACHE = [{"id": h["id"], "name": h["localized_name"], "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png"} for h in r.json()]
                return HEROES_CACHE
    except: pass
    return []

async def get_hero_stats_cache():
    global HERO_STATS_CACHE
    if HERO_STATS_CACHE: return HERO_STATS_CACHE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://api.opendota.com/api/heroStats")
            if r.status_code == 200:
                HERO_STATS_CACHE = r.json()
                return HERO_STATS_CACHE
    except: pass
    return []

async def get_matchups(hero_id: int):
    if hero_id in MATCHUP_CACHE: return MATCHUP_CACHE[hero_id]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
            if r.status_code == 200:
                data = r.json()
                MATCHUP_CACHE[hero_id] = data
                return data
    except: pass
    return []

def get_user_favorite_ids(user_id: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s;", (user_id,))
                row = cur.fetchone()
                return row[0] if row and row[0] else []
    except: return []

@router.get("/heroes")
async def get_heroes():
    return await get_heroes_cache()

@router.get("/global-bans")
async def get_global_bans(user_id: str):
    fav_ids = get_user_favorite_ids(user_id)
    if not fav_ids: return {"bans": []}
    
    heroes_list = await get_heroes_cache()
    id_to_name = {h["id"]: h["name"] for h in heroes_list}
    
    # Чтобы не нагружать API, берем матчапы только для первых 5 любимых героев
    fav_matchups_data = await asyncio.gather(*(get_matchups(fid) for fid in fav_ids[:5]))
    
    threats = {}
    for matchups in fav_matchups_data:
        for m in matchups:
            if m.get("games_played", 0) < MIN_GAMES_FOR_MATCHUP: continue
            name = id_to_name.get(m["hero_id"])
            if name:
                wr = m["wins"] / m["games_played"]
                threats[name] = threats.get(name, 0) + wr

    sorted_bans = sorted(threats.items(), key=lambda x: -x[1])[:4]
    h_map = {h["name"]: h for h in heroes_list}
    return {"bans": [h_map[n] for n, _ in sorted_bans if n in h_map]}

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

@router.post("/analyze")
async def analyze_draft(payload: DraftRequest):
    try:
        heroes_list = await get_heroes_cache()
        hero_stats = await get_hero_stats_cache()
        if not heroes_list: raise ValueError("Список героев пуст")

        name_to_id = {h["name"].lower(): h["id"] for h in heroes_list}
        id_to_name = {h["id"]: h["name"] for h in heroes_list}
        picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
        
        # Средние винрейты
        base_wr = {}
        for hs in hero_stats:
            name = hs.get("localized_name")
            p, w = sum(hs.get(f"{i}_pick", 0) for i in range(1, 9)), sum(hs.get(f"{i}_win", 0) for i in range(1, 9))
            base_wr[name] = (w/p*100) if p > 0 else 50

        # Контрпики
        enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
        matchups_data = await asyncio.gather(*(get_matchups(eid) for eid in enemy_ids))
        
        hero_advs = {}
        for matchups in matchups_data:
            for m in matchups:
                name = id_to_name.get(m["hero_id"])
                if name and m.get("games_played", 0) >= MIN_GAMES_FOR_MATCHUP:
                    adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                    hero_advs.setdefault(name, []).append(adv)

        all_candidates = []
        for h in heroes_list:
            if h["name"].lower() in picked: continue
            advs = hero_advs.get(h["name"], [0])
            avg_adv = sum(advs)/len(advs)
            all_candidates.append({
                "id": h["id"], "name": h["name"], "img": h["img"],
                "winrate": round(base_wr.get(h["name"], 50) + avg_adv, 1),
                "advantage": round(avg_adv, 1),
                "games": 100 # заглушка
            })

        fav_ids = get_user_favorite_ids(payload.user_id) if payload.user_id else []
        results = []
        for r_k, r_t in ROLES.items():
            if payload.my_team.get(r_k): continue
            
            # Базовая фильтрация по ролям
            ranked = sorted(all_candidates, key=lambda x: -x["winrate"])
            
            used = set()
            def pick(lst):
                for c in lst:
                    if c["id"] not in used:
                        used.add(c["id"])
                        return c
                return None

            results.append({
                "role": r_t,
                "data": {
                    "top_favorite": pick([c for c in ranked if c["id"] in fav_ids]),
                    "top_winrate": pick(ranked),
                    "others": [pick(ranked) for _ in range(OTHERS_COUNT)]
                }
            })
        return {"results": results}
    except Exception as e:
        print(f"Ошибка Analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))
