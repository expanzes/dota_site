import asyncio, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection

router = APIRouter()

# Кэш для ускорения работы
HEROES_CACHE = []
HERO_STATS_CACHE = []
MATCHUP_CACHE = {}

ROLES = {
    "pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", 
    "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"
}

# Расширенная карта позиций (Актуальная мета)
HERO_POSITIONS = {
    "Abaddon": [3, 4, 5], "Alchemist": [1, 2], "Ancient Apparition": [4, 5], "Anti-Mage": [1],
    "Arc Warden": [1, 2], "Axe": [3], "Bane": [5], "Batrider": [2, 3, 4], "Beastmaster": [3],
    "Bloodseeker": [1, 2], "Bounty Hunter": [4], "Brewmaster": [3], "Bristleback": [3],
    "Broodmother": [1, 2, 3], "Centaur Warrunner": [3], "Chaos Knight": [1, 3], "Chen": [5],
    "Clinkz": [1, 2, 4], "Clockwerk": [4], "Crystal Maiden": [5], "Dark Seer": [3],
    "Dark Willow": [4, 5], "Dawnbreaker": [3, 4], "Dazzle": [5], "Death Prophet": [2, 3],
    "Disruptor": [5], "Doom": [3], "Dragon Knight": [2, 3], "Drow Ranger": [1], "Earth Spirit": [4],
    "Earthshaker": [4], "Elder Titan": [4, 5], "Ember Spirit": [2], "Enchantress": [4, 5],
    "Enigma": [3, 4], "Faceless Void": [1], "Grimstroke": [4, 5], "Gyrocopter": [1, 4],
    "Hoodwink": [4], "Huskar": [2], "Invoker": [2], "Io": [5], "Jakiro": [5],
    "Juggernaut": [1], "Keeper of the Light": [2, 4], "Kez": [1, 2], "Kunkka": [2, 3],
    "Legion Commander": [3], "Leshrac": [2], "Lich": [5], "Lifestealer": [1], "Lina": [2, 4],
    "Lion": [4, 5], "Luna": [1], "Lycan": [3], "Magnus": [2, 3], "Marci": [4],
    "Mars": [3], "Medusa": [1], "Meepo": [1, 2], "Mirana": [4], "Monkey King": [1, 2],
    "Morphling": [1], "Muerta": [1], "Naga Siren": [1], "Nature's Prophet": [2, 3, 4],
    "Necrophos": [2, 3], "Night Stalker": [3], "Nyx Assassin": [4], "Ogre Magi": [5],
    "Omniknight": [3, 5], "Oracle": [5], "Outworld Destroyer": [2], "Pangolier": [2, 3],
    "Phantom Assassin": [1], "Phantom Lancer": [1], "Primal Beast": [2, 3], "Puck": [2],
    "Pudge": [1, 3, 4], "Pugna": [2, 4, 5], "Queen of Pain": [2], "Razor": [1, 3],
    "Riki": [1], "Ringmaster": [4, 5], "Rubick": [4], "Sand King": [3], "Shadow Demon": [5],
    "Shadow Fiend": [1, 2], "Shadow Shaman": [5], "Silencer": [4, 5], "Skywrath Mage": [4, 5],
    "Slardar": [3], "Slark": [1], "Snapfire": [2, 4], "Sniper": [1, 2], "Spectre": [1],
    "Spirit Breaker": [4], "Storm Spirit": [2], "Sven": [1], "Techies": [4], "Templar Assassin": [1, 2],
    "Terrorblade": [1], "Tidehunter": [3], "Timbersaw": [2, 3], "Tinker": [2, 4], "Tiny": [2, 4],
    "Treant Protector": [5], "Troll Warlord": [1], "Tusk": [4], "Underlord": [3], "Undying": [5],
    "Ursa": [1], "Vengeful Spirit": [4, 5], "Venomancer": [3, 4, 5], "Viper": [2, 3],
    "Visage": [2, 3], "Void Spirit": [2], "Warlock": [5], "Weaver": [1, 4], "Windranger": [2, 4],
    "Winter Wyvern": [5], "Witch Doctor": [5], "Wraith King": [1, 3], "Zeus": [2, 4]
}

async def get_matchups_data(hero_id: int):
    if hero_id in MATCHUP_CACHE: return MATCHUP_CACHE[hero_id]
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
            if r.status_code == 200:
                data = r.json()
                MATCHUP_CACHE[hero_id] = data
                return data
        except: return []
    return []

def get_db_favs(user_id: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
                return row[0] if row and row[0] else []
    except: return []

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

@router.get("/heroes")
async def heroes_endpoint():
    async with httpx.AsyncClient() as c:
        r = await c.get("https://api.opendota.com/api/heroes")
        data = r.json()
        return [{"id": h["id"], "name": h["localized_name"], "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png"} for h in data]

@router.post("/analyze")
async def analyze_perfect(payload: DraftRequest):
    try:
        async with httpx.AsyncClient() as c:
            h_res, s_res = await asyncio.gather(c.get("https://api.opendota.com/api/heroes"), c.get("https://api.opendota.com/api/heroStats"))
        
        h_list = h_res.json()
        h_stats = s_res.json()
        
        id_to_name = {h["id"]: h["localized_name"] for h in h_list}
        name_to_id = {h["localized_name"].lower(): h["id"] for h in h_list}
        img_map = {h["localized_name"]: f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png" for h in h_list}
        
        picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
        
        # 1. Immortal Winrate
        base_wr = {}
        for hs in h_stats:
            p = hs.get("8_pick", 0) # 8 rank = Immortal
            w = hs.get("8_win", 0)
            base_wr[hs["localized_name"]] = (w/p*100) if p > 30 else (hs.get("7_win", 1)/hs.get("7_pick", 1)*100)

        # 2. Matchup Data
        enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
        ally_ids = [name_to_id[n.lower()] for n in payload.my_team.values() if n and n.lower() in name_to_id]

        enemies_results = await asyncio.gather(*(get_matchups_data(eid) for eid in enemy_ids))
        allies_results = await asyncio.gather(*(get_matchups_data(aid) for aid in ally_ids))

        # 3. Processing
        hero_scores = []
        for h in h_list:
            name = h["localized_name"]
            if name.lower() in picked: continue
            
            # Counter Score
            c_score = 0
            is_hard_countered = False
            for m_list in enemies_results:
                for m in m_list:
                    if m["hero_id"] == h["id"] and m["games_played"] > 10:
                        adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                        if adv < -5.5: 
                            c_score += adv * 3.0 # Критический штраф
                            is_hard_countered = True
                        else: c_score += adv

            # Synergy Score
            s_score = 0
            for m_list in allies_results:
                for m in m_list:
                    if m["hero_id"] == h["id"] and m["games_played"] > 10:
                        adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                        s_score += adv * 0.7 # Синергия важна, но вторична

            final_wr = base_wr.get(name, 50) + c_score + s_score
            if is_hard_countered: final_wr -= 12 # Доп штраф за "неиграбельность"

            hero_scores.append({
                "id": h["id"], "name": name, "img": img_map.get(name),
                "winrate": round(final_wr, 1),
                "advantage": round(c_score + s_score, 1)
            })

        # 4. Results by Position
        fav_ids = get_db_favs(payload.user_id) if payload.user_id else []
        final_results = []
        for r_k, r_t in ROLES.items():
            if payload.my_team.get(r_k): continue
            
            pos = int(r_k[-1])
            eligible = [c for c in hero_scores if pos in HERO_POSITIONS.get(c["name"], [1,2,3,4,5])]
            ranked = sorted(eligible, key=lambda x: -x["winrate"])
            
            used = set()
            def pick(lst):
                for c in lst:
                    if c["id"] not in used:
                        used.add(c["id"])
                        return c
                return None

            final_results.append({
                "role": r_t,
                "data": {
                    "top_favorite": pick([c for c in ranked if c["id"] in fav_ids]),
                    "top_winrate": pick(ranked),
                    "others": [pick(ranked) for _ in range(3)]
                }
            })
        return {"results": final_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
