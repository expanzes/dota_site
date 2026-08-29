import asyncio, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection

router = APIRouter()
HEROES_CACHE, HERO_STATS_CACHE, MATCHUP_CACHE = [], [], {}
ROLES = {"pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"}

async def fetch_opendota(path: str):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"https://api.opendota.com/api{path}")
        return r.json() if r.status_code == 200 else None

async def get_heroes():
    global HEROES_CACHE
    if not HEROES_CACHE:
        data = await fetch_opendota("/heroes")
        if data: HEROES_CACHE = [{"id": h["id"], "name": h["localized_name"], "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png"} for h in data]
    return HEROES_CACHE

async def get_matchups(hero_id: int):
    if hero_id not in MATCHUP_CACHE:
        data = await fetch_opendota(f"/heroes/{hero_id}/matchups")
        if data: MATCHUP_CACHE[hero_id] = data
    return MATCHUP_CACHE.get(hero_id, [])

@router.get("/heroes")
async def heroes_endpoint(): return await get_heroes()

@router.get("/global-bans")
async def get_global_bans(user_id: str):
    from routers.auth import get_favorites
    favs = (await get_favorites(user_id))["favorite_ids"]
    if not favs: return {"bans": []}
    
    h_list = await get_heroes()
    id_to_name = {h["id"]: h["name"] for h in h_list}
    all_matchups = await asyncio.gather(*(get_matchups(fid) for fid in favs[:5]))
    
    threats = {}
    for m_list in all_matchups:
        for m in m_list:
            if m.get("games_played", 0) > 20:
                name = id_to_name.get(m["hero_id"])
                if name: threats[name] = threats.get(name, 0) + (m["wins"]/m["games_played"])

    sorted_bans = sorted(threats.items(), key=lambda x: -x[1])[:4]
    h_map = {h["name"]: h for h in h_list}
    return {"bans": [h_map[n] for n, _ in sorted_bans if n in h_map]}

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

@router.post("/analyze")
async def analyze(payload: DraftRequest):
    h_list = await get_heroes()
    h_stats = await fetch_opendota("/hero_stats") or []
    id_to_name = {h["id"]: h["name"] for h in h_list}
    name_to_id = {h["name"].lower(): h["id"] for h in h_list}
    picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}

    base_wr = {hs["localized_name"]: (hs.get("8_win", 0)/hs.get("8_pick", 1)*100) for hs in h_stats if "localized_name" in hs}
    
    enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
    matchups_results = await asyncio.gather(*(get_matchups(eid) for eid in enemy_ids))
    
    hero_advs = {}
    for m_list in matchups_results:
        for m in m_list:
            name = id_to_name.get(m["hero_id"])
            if name and m.get("games_played", 0) > 20:
                adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                hero_advs.setdefault(name, []).append(adv)

    all_c = []
    for h in h_list:
        if h["name"].lower() in picked: continue
        advs = hero_advs.get(h["name"], [0])
        avg_adv = sum(advs)/len(advs)
        all_c.append({"id": h["id"], "name": h["name"], "img": h["img"], "winrate": round(base_wr.get(h["name"], 50) + avg_adv, 1), "advantage": round(avg_adv, 1)})

    from routers.auth import get_favorites
    fav_ids = (await get_favorites(payload.user_id))["favorite_ids"] if payload.user_id else []
    
    results = []
    for r_k, r_t in ROLES.items():
        if payload.my_team.get(r_k): continue
        ranked = sorted(all_c, key=lambda x: -x["winrate"])
        results.append({"role": r_t, "data": {
            "top_favorite": next((c for c in ranked if c["id"] in fav_ids), None),
            "top_winrate": ranked[0] if ranked else None,
            "others": ranked[1:4]
        }})
    return {"results": results}
