import asyncio, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection

router = APIRouter()
HEROES_CACHE, HERO_STATS_CACHE, MATCHUP_CACHE = [], [], {}
ROLES = {"pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"}

HERO_POSITIONS = {
    "Abaddon": [3, 4, 5], "Alchemist": [1, 3], "Ancient Apparition": [4, 5], "Anti-Mage": [1], "Arc Warden": [1, 2], "Axe": [3], "Bane": [4, 5], "Batrider": [2, 3], "Beastmaster": [3], "Bloodseeker": [1, 2], "Bounty Hunter": [4], "Brewmaster": [3], "Bristleback": [3], "Broodmother": [1, 2, 3], "Centaur Warrunner": [3], "Chaos Knight": [1], "Chen": [5], "Clinkz": [1, 2, 3], "Clockwerk": [3, 4], "Crystal Maiden": [5], "Dark Seer": [3], "Dark Willow": [4, 5], "Dawnbreaker": [3, 4], "Dazzle": [4, 5], "Death Prophet": [2, 3], "Disruptor": [5], "Doom": [3], "Dragon Knight": [2, 3], "Drow Ranger": [1], "Earth Spirit": [3, 4], "Earthshaker": [3, 4], "Elder Titan": [3, 4], "Ember Spirit": [2], "Enchantress": [4, 5], "Enigma": [3, 4], "Faceless Void": [1], "Grimstroke": [4, 5], "Gyrocopter": [1, 2], "Hoodwink": [4, 5], "Huskar": [1, 2], "Invoker": [2], "Io": [5], "Jakiro": [4, 5], "Juggernaut": [1], "Keeper of the Light": [4, 5], "Kez": [1, 2], "Kunkka": [2, 3], "Legion Commander": [3], "Leshrac": [2, 3], "Lich": [4, 5], "Lifestealer": [1], "Lina": [2, 4], "Lion": [4, 5], "Luna": [1], "Lycan": [1, 3], "Magnus": [2, 3], "Marci": [3, 4], "Mars": [3], "Medusa": [1], "Meepo": [1, 2], "Mirana": [2, 4], "Monkey King": [1, 2, 3], "Morphling": [1], "Muerta": [2, 5], "Naga Siren": [1], "Nature's Prophet": [2, 3], "Necrophos": [2, 3], "Night Stalker": [3], "Nyx Assassin": [3, 4], "Ogre Magi": [4, 5], "Omniknight": [4, 5], "Oracle": [4, 5], "Outworld Destroyer": [2, 3], "Pangolier": [2, 3], "Phantom Assassin": [1], "Phantom Lancer": [1], "Primal Beast": [3, 4], "Puck": [2], "Pudge": [3, 4], "Pugna": [2, 5], "Queen of Pain": [2], "Razor": [1, 2, 3], "Riki": [1, 3, 4], "Ringmaster": [4, 5], "Rubick": [4, 5], "Sand King": [3], "Shadow Demon": [4, 5], "Shadow Fiend": [2], "Shadow Shaman": [4, 5], "Silencer": [4, 5], "Skywrath Mage": [4, 5], "Slardar": [3], "Slark": [1], "Snapfire": [4, 5], "Sniper": [1, 2], "Spectre": [1], "Spirit Breaker": [3, 4], "Storm Spirit": [2], "Sven": [1, 3], "Techies": [4, 5], "Templar Assassin": [2], "Terrorblade": [1], "Tidehunter": [3], "Timbersaw": [3], "Tinker": [2], "Tiny": [1, 3], "Treant Protector": [4, 5], "Troll Warlord": [1], "Tusk": [3, 4], "Underlord": [3], "Undying": [4, 5], "Ursa": [1, 2, 3], "Vengeful Spirit": [4, 5], "Venomancer": [3, 4], "Viper": [2, 3], "Visage": [4, 5], "Void Spirit": [2, 3], "Warlock": [4, 5], "Weaver": [1, 2, 4], "Windranger": [2, 4], "Winter Wyvern": [4, 5], "Witch Doctor": [4, 5], "Wraith King": [1, 3], "Zeus": [2, 4],
}

async def get_heroes_cache():
    global HEROES_CACHE
    if HEROES_CACHE: return HEROES_CACHE
    async with httpx.AsyncClient() as c:
        r = await c.get("https://api.opendota.com/api/heroes")
        if r.status_code == 200:
            HEROES_CACHE = [{"id": h["id"], "name": h["localized_name"], "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png"} for h in r.json()]
    return HEROES_CACHE

async def get_matchups(hero_id: int):
    if hero_id in MATCHUP_CACHE: return MATCHUP_CACHE[hero_id]
    async with httpx.AsyncClient() as c:
        r = await c.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
        if r.status_code == 200: MATCHUP_CACHE[hero_id] = r.json()
    return MATCHUP_CACHE.get(hero_id, [])

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

@router.get("/heroes")
async def heroes_endpoint(): return await get_heroes_cache()

@router.post("/analyze")
async def analyze(payload: DraftRequest):
    h_list = await get_heroes_cache()
    async with httpx.AsyncClient() as c:
        stats_res = await c.get("https://api.opendota.com/api/heroStats")
        h_stats = stats_res.json() if stats_res.status_code == 200 else []
    
    name_to_id = {h["name"].lower(): h["id"] for h in h_list}
    id_to_name = {h["id"]: h["name"] for h in h_list}
    picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
    
    base_wr = {hs["localized_name"]: (sum(hs.get(f"{i}_win", 0) for i in range(1, 9)) / sum(hs.get(f"{i}_pick", 0) for i in range(1, 9)) * 100) if sum(hs.get(f"{i}_pick", 0) for i in range(1, 9)) else 50 for hs in h_stats}
    
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
        adv_list = hero_advs.get(h["name"], [0])
        avg_adv = sum(adv_list)/len(adv_list)
        all_c.append({"id": h["id"], "name": h["name"], "img": h["img"], "winrate": round(base_wr.get(h["name"], 50) + avg_adv, 1), "advantage": round(avg_adv, 1)})

    fav_ids = []
    if payload.user_id:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s", (payload.user_id,))
                row = cur.fetchone()
                fav_ids = row[0] if row and row[0] else []

    results = []
    for r_k, r_t in ROLES.items():
        if payload.my_team.get(r_k): continue
        pos = int(r_k[-1])
        eligible = [c for c in all_c if pos in HERO_POSITIONS.get(c["name"], [1,2,3,4,5])]
        ranked = sorted(eligible, key=lambda x: -x["winrate"])
        results.append({"role": r_t, "data": {
            "top_favorite": next((c for c in ranked if c["id"] in fav_ids), None),
            "top_winrate": ranked[0] if ranked else None,
            "others": ranked[1:4]
        }})
    return {"results": results}
