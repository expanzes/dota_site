import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
import httpx
from routers.auth import get_db_connection

router = APIRouter()

HEROES_CACHE: List[dict] = []
HERO_STATS_CACHE: List[dict] = []
MATCHUP_CACHE: Dict[int, List[dict]] = {}
LANE_ROLES_CACHE: Dict[int, Dict[int, int]] = {}

MIN_GAMES_FOR_RANK = 50
MIN_GAMES_FOR_MATCHUP = 30
OTHERS_COUNT = 3
MIN_LANE_SHARE = 0.10

ROLES = {
    "pos1": "Поз 1 (Керри)",
    "pos2": "Поз 2 (Мид)",
    "pos3": "Поз 3 (Тройка)",
    "pos4": "Поз 4 (Четверка)",
    "pos5": "Поз 5 (Пятерка)",
}

FALLBACK_HEROES = [
    {"id": 1, "name": "Anti-Mage", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png"},
    {"id": 14, "name": "Pudge", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/pudge.png"},
    {"id": 74, "name": "Invoker", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/invoker.png"},
]

HERO_POSITIONS: Dict[str, List[int]] = {
    "Abaddon": [3, 4, 5], "Alchemist": [1, 3], "Ancient Apparition": [4, 5],
    "Anti-Mage": [1], "Arc Warden": [1, 2], "Axe": [3], "Bane": [4, 5],
    "Batrider": [2, 3], "Beastmaster": [3], "Bloodseeker": [1, 2],
    "Bounty Hunter": [4], "Brewmaster": [3], "Bristleback": [3],
    "Broodmother": [1, 2, 3], "Centaur Warrunner": [3], "Chaos Knight": [1],
    "Chen": [5], "Clinkz": [1, 2, 3], "Clockwerk": [3, 4], "Crystal Maiden": [5],
    "Dark Seer": [3], "Dark Willow": [4, 5], "Dawnbreaker": [3, 4],
    "Dazzle": [4, 5], "Death Prophet": [2, 3], "Disruptor": [5], "Doom": [3],
    "Dragon Knight": [2, 3], "Drow Ranger": [1], "Earth Spirit": [3, 4],
    "Earthshaker": [3, 4], "Elder Titan": [3, 4], "Ember Spirit": [2],
    "Enchantress": [4, 5], "Enigma": [3, 4], "Faceless Void": [1],
    "Grimstroke": [4, 5], "Gyrocopter": [1, 2], "Hoodwink": [4, 5],
    "Huskar": [1, 2], "Invoker": [2], "Io": [5], "Jakiro": [4, 5],
    "Juggernaut": [1], "Keeper of the Light": [4, 5], "Kez": [1, 2],
    "Kunkka": [2, 3], "Legion Commander": [3], "Leshrac": [2, 3],
    "Lich": [4, 5], "Lifestealer": [1], "Lina": [2, 4], "Lion": [4, 5],
    "Luna": [1], "Lycan": [1, 3], "Magnus": [2, 3], "Marci": [3, 4],
    "Mars": [3], "Medusa": [1], "Meepo": [1, 2], "Mirana": [2, 4],
    "Monkey King": [1, 2, 3], "Morphling": [1], "Muerta": [2, 5],
    "Naga Siren": [1], "Nature's Prophet": [2, 3], "Necrophos": [2, 3],
    "Night Stalker": [3], "Nyx Assassin": [3, 4], "Ogre Magi": [4, 5],
    "Omniknight": [4, 5], "Oracle": [4, 5], "Outworld Destroyer": [2, 3],
    "Pangolier": [2, 3], "Phantom Assassin": [1], "Phantom Lancer": [1],
    "Primal Beast": [3, 4], "Puck": [2], "Pudge": [3, 4], "Pugna": [2, 5],
    "Queen of Pain": [2], "Razor": [1, 2, 3], "Riki": [1, 3, 4],
    "Ringmaster": [4, 5], "Rubick": [4, 5], "Sand King": [3],
    "Shadow Demon": [4, 5], "Shadow Fiend": [2], "Shadow Shaman": [4, 5],
    "Silencer": [4, 5], "Skywrath Mage": [4, 5], "Slardar": [3],
    "Slark": [1], "Snapfire": [4, 5], "Sniper": [1, 2], "Spectre": [1],
    "Spirit Breaker": [3, 4], "Storm Spirit": [2], "Sven": [1, 3],
    "Techies": [4, 5], "Templar Assassin": [2], "Terrorblade": [1],
    "Tidehunter": [3], "Timbersaw": [3], "Tinker": [2], "Tiny": [1, 3],
    "Treant Protector": [4, 5], "Troll Warlord": [1], "Tusk": [3, 4],
    "Underlord": [3], "Undying": [4, 5], "Ursa": [1, 2, 3],
    "Vengeful Spirit": [4, 5], "Venomancer": [3, 4], "Viper": [2, 3],
    "Visage": [4, 5], "Void Spirit": [2, 3], "Warlock": [4, 5],
    "Weaver": [1, 2, 4], "Windranger": [2, 4], "Winter Wyvern": [4, 5],
    "Witch Doctor": [4, 5], "Wraith King": [1, 3], "Zeus": [2, 4],
}

LANE_SAFE, LANE_MID, LANE_OFF = 1, 2, 3
LANE_FOR_POSITION = {1: {LANE_SAFE}, 2: {LANE_MID}, 3: {LANE_OFF}, 4: {LANE_SAFE, LANE_OFF}, 5: {LANE_SAFE}}

def positions_for_hero(hero_name: str, hero_id: int, lane_stats: Dict[int, Dict[int, int]]) -> List[int]:
    base = HERO_POSITIONS.get(hero_name, [1, 2, 3, 4, 5])
    stats = lane_stats.get(hero_id)
    if not stats or sum(stats.values()) == 0: return base
    total = sum(stats.values())
    res = [p for p in base if sum(stats.get(l, 0) for l in LANE_FOR_POSITION.get(p, {1, 2, 3})) / total >= MIN_LANE_SHARE]
    return res if res else base

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
    return FALLBACK_HEROES

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

async def get_lane_roles_cache():
    global LANE_ROLES_CACHE
    if LANE_ROLES_CACHE: return LANE_ROLES_CACHE
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://api.opendota.com/api/scenarios/laneRoles")
            if r.status_code == 200:
                agg = {}
                for row in r.json():
                    h_id, l_r, g = row.get("hero_id"), row.get("lane_role"), row.get("games", 0) or 0
                    if h_id and l_r: agg.setdefault(h_id, {})[l_r] = agg[h_id].get(l_r, 0) + g
                LANE_ROLES_CACHE = agg
                return agg
    except: pass
    return {}

async def get_matchups(hero_id: int):
    if hero_id in MATCHUP_CACHE: return MATCHUP_CACHE[hero_id]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
            if r.status_code == 200:
                MATCHUP_CACHE[hero_id] = r.json()
                return MATCHUP_CACHE[hero_id]
    except: pass
    return []

def get_user_favorite_ids(user_id: Optional[str]):
    if not user_id: return []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s;", (user_id,))
                row = cur.fetchone()
                return row[0] if row and row[0] else []
    except: return []

@router.get("/heroes")
async def get_heroes(): return await get_heroes_cache()

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

def format_hero(candidate: dict):
    return {
        "name": candidate["name"],
        "winrate": candidate["winrate"],
        "advantage": candidate["advantage"], # Добавили поле преимущества
        "games": candidate["games"],
        "img": candidate["img"]
    }

@router.post("/analyze")
async def analyze_draft(payload: DraftRequest):
    heroes_list = await get_heroes_cache()
    hero_stats = await get_hero_stats_cache()
    lane_stats = await get_lane_roles_cache()
    
    name_to_id = {h["name"].lower(): h["id"] for h in heroes_list}
    id_to_name = {h["id"]: h["name"] for h in heroes_list}
    picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
    
    base_wr, base_gm = {}, {}
    for hs in hero_stats:
        name = hs.get("localized_name")
        if not name: continue
        tp = sum(hs.get(f"{i}_pick", 0) or 0 for i in range(1, 9))
        tw = sum(hs.get(f"{i}_win", 0) or 0 for i in range(1, 9))
        base_wr[name] = (tw / tp * 100) if tp else 50
        base_gm[name] = tp

    enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
    matchups_data = await asyncio.gather(*(get_matchups(eid) for eid in enemy_ids))
    
    # Считаем суммарный Advantage для каждого возможного героя
    hero_advantages = {} # name -> sum_advantage
    for matchups in matchups_data:
        for m in matchups:
            games = m.get("games_played", 0)
            if games < MIN_GAMES_FOR_MATCHUP: continue
            c_name = id_to_name.get(m.get("hero_id"))
            if not c_name or c_name.lower() in picked: continue
            
            # Винрейт кандидата конкретно в этом матчапе
            wr_vs_enemy = 100 - (m.get("wins", 0) / games * 100)
            # Advantage = (Винрейт в матчапе) - (Средний винрейт)
            adv = wr_vs_enemy - base_wr.get(c_name, 50)
            
            hero_advantages.setdefault(c_name, []).append(adv)

    all_candidates = []
    for h in heroes_list:
        name = h["name"]
        if name.lower() in picked: continue
        
        avg_wr = base_wr.get(name, 50)
        # Итоговый бонус — это среднее арифметическое преимуществ против всех врагов
        adv_list = hero_advantages.get(name, [0])
        total_adv = sum(adv_list) / len(adv_list) if adv_list else 0
        
        # Итоговый "драфт-винрейт" для сортировки
        final_score = avg_wr + total_adv

        all_candidates.append({
            "id": h["id"],
            "name": name,
            "img": h["img"],
            "winrate": round(final_score, 1),
            "advantage": round(total_adv, 1), # Сохраняем чистое преимущество
            "games": base_gm.get(name, 0)
        })

    fav_ids = get_user_favorite_ids(payload.user_id)
    results = []
    for r_k, r_t in ROLES.items():
        if payload.my_team.get(r_k): continue
        
        # Фильтруем кандидатов по позиции
        eligible = [c for c in all_candidates if int(r_k[-1]) in positions_for_hero(c["name"], c["id"], lane_stats)]
        pool = [c for c in eligible if c["games"] >= MIN_GAMES_FOR_RANK] or eligible
        
        # Сортируем по итоговому скору (винрейт + преимущество)
        ranked = sorted(pool, key=lambda c: -c["winrate"])
        
        used = set()
        def pick(lst):
            for c in lst:
                if c["id"] not in used: 
                    used.add(c["id"])
                    return format_hero(c)
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
