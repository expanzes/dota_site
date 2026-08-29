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

LANE_SAFE = 1
LANE_MID = 2
LANE_OFF = 3

LANE_FOR_POSITION: Dict[int, set] = {
    1: {LANE_SAFE}, 2: {LANE_MID}, 3: {LANE_OFF},
    4: {LANE_SAFE, LANE_OFF}, 5: {LANE_SAFE},
}

def positions_for_hero(hero_name: str, hero_id: int, lane_stats: Dict[int, Dict[int, int]]) -> List[int]:
    base_positions = HERO_POSITIONS.get(hero_name, [1, 2, 3, 4, 5])
    hero_lane_games = lane_stats.get(hero_id)
    if not hero_lane_games: return base_positions
    total_games = sum(hero_lane_games.values())
    if total_games == 0: return base_positions
    result = []
    for pos in base_positions:
        allowed_lanes = LANE_FOR_POSITION.get(pos, {LANE_SAFE, LANE_MID, LANE_OFF})
        games_on_allowed_lanes = sum(hero_lane_games.get(l, 0) for l in allowed_lanes)
        if (games_on_allowed_lanes / total_games) >= MIN_LANE_SHARE:
            result.append(pos)
    return result if result else base_positions

async def get_heroes_cache() -> List[dict]:
    global HEROES_CACHE
    if HEROES_CACHE: return HEROES_CACHE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.opendota.com/api/heroes")
            if response.status_code == 200:
                data = response.json()
                HEROES_CACHE = [{"id": h["id"], "name": h["localized_name"], "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png"} for h in data]
                return HEROES_CACHE
    except: pass
    return FALLBACK_HEROES

async def get_hero_stats_cache() -> List[dict]:
    global HERO_STATS_CACHE
    if HERO_STATS_CACHE: return HERO_STATS_CACHE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.opendota.com/api/heroStats")
            if response.status_code == 200:
                HERO_STATS_CACHE = response.json()
                return HERO_STATS_CACHE
    except: pass
    return []

async def get_lane_roles_cache() -> Dict[int, Dict[int, int]]:
    global LANE_ROLES_CACHE
    if LANE_ROLES_CACHE: return LANE_ROLES_CACHE
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.opendota.com/api/scenarios/laneRoles")
            if response.status_code == 200:
                raw_rows = response.json()
                aggregated: Dict[int, Dict[int, int]] = {}
                for row in raw_rows:
                    hero_id, lane_role, games = row.get("hero_id"), row.get("lane_role"), row.get("games", 0) or 0
                    if hero_id is None or lane_role is None: continue
                    aggregated.setdefault(hero_id, {})[lane_role] = aggregated[hero_id].get(lane_role, 0) + games
                LANE_ROLES_CACHE = aggregated
                return LANE_ROLES_CACHE
    except: pass
    return {}

async def get_matchups(hero_id: int) -> List[dict]:
    if hero_id in MATCHUP_CACHE: return MATCHUP_CACHE[hero_id]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
            if response.status_code == 200:
                MATCHUP_CACHE[hero_id] = response.json()
                return MATCHUP_CACHE[hero_id]
    except: pass
    return []

def get_user_favorite_ids(user_id: Optional[str]) -> List[int]:
    if not user_id: return []
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

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

def format_hero(candidate: Optional[dict]) -> Optional[dict]:
    if not candidate: return None
    return {"name": candidate["name"], "winrate": candidate["winrate"], "games": candidate["games"], "img": candidate["img"]}

def build_recommendation_pool_for_position(all_candidates: List[dict], pos_num: int, favorite_ids: List[int], lane_stats: Dict[int, Dict[int, int]]) -> dict:
    eligible = [c for c in all_candidates if pos_num in positions_for_hero(c["name"], c["id"], lane_stats)]
    pool_source = eligible if eligible else all_candidates
    reliable = [c for c in pool_source if c["games"] >= MIN_GAMES_FOR_RANK]
    pool = reliable if reliable else pool_source
    ranked = sorted(pool, key=lambda c: -c["winrate"])
    used_ids = set()
    def take_first(lst):
        for c in lst:
            if c["id"] not in used_ids:
                used_ids.add(c["id"])
                return c
        return None
    top_winrate = take_first(ranked)
    top_fav = take_first([c for c in ranked if c["id"] in favorite_ids]) if favorite_ids else None
    others = [c for c in ranked if c["id"] not in used_ids][:OTHERS_COUNT]
    return {"top_favorite": format_hero(top_fav), "top_winrate": format_hero(top_winrate), "others": [format_hero(c) for c in others]}

@router.post("/analyze")
async def analyze_draft(payload: DraftRequest):
    heroes_list = await get_heroes_cache()
    hero_stats = await get_hero_stats_cache()
    lane_stats = await get_lane_roles_cache()
    name_to_id = {h["name"].lower(): h["id"] for h in heroes_list}
    id_to_name = {h["id"]: h["name"] for h in heroes_list}
    picked_names = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
    base_wr, base_gm = {}, {}
    for hs in hero_stats:
        name = hs.get("localized_name")
        if not name: continue
        tp = sum(hs.get(f"{i}_pick", 0) or 0 for i in range(1, 9))
        tw = sum(hs.get(f"{i}_win", 0) or 0 for i in range(1, 9))
        base_wr[name], base_gm[name] = (tw/tp*100 if tp else 0), tp
    enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
    matchups_data = await asyncio.gather(*(get_matchups(eid) for eid in enemy_ids))
    counters = {}
    for matchups in matchups_data:
        for m in matchups:
            games = m.get("games_played", 0)
            if games < MIN_GAMES_FOR_MATCHUP: continue
            c_name = id_to_name.get(m.get("hero_id"))
            if not c_name: continue
            c_wr = 100 - (m.get("wins", 0) / games * 100)
            entry = counters.setdefault(c_name, [0.0, 0.0])
            entry[0] += c_wr * games
            entry[1] += games
    all_candidates = []
    for h in heroes_list:
        name = h["name"]
        if name.lower() in picked_names: continue
        base, games = base_wr.get(name, 50), base_gm.get(name, 0)
        if name in counters and counters[name][1] > 0:
            c_wr = counters[name][0] / counters[name][1]
            w = min(len(enemy_ids)/5, 1.0) * 0.7
            final_wr = c_wr * w + base * (1-w)
        else: final_wr = base
        all_candidates.append({"id": h["id"], "name": name, "img": h["img"], "winrate": round(final_wr, 1), "games": games})
    fav_ids = get_user_favorite_ids(payload.user_id)
    results = []
    for r_k, r_t in ROLES.items():
        if payload.my_team.get(r_k): continue
        results.append({"role": r_t, "data": build_recommendation_pool_for_position(all_candidates, int(r_k[-1]), fav_ids, lane_stats)})
    return {"results": results}
