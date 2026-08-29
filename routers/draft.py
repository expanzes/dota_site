import asyncio, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection

router = APIRouter()
MATCHUP_CACHE = {}

ROLES = {"pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"}

# --- ПОЛНАЯ БАЗА ТЕГОВ (127 ГЕРОЕВ) ---
# [Контроль, Стойкость, Инициация, Урон, Осада, Побег] (0-3)
HERO_TAGS = {
    "Abaddon": [1,3,1,1,1,1], "Alchemist": [1,2,1,2,3,1], "Ancient Apparition": [1,0,0,3,0,0], "Anti-Mage": [0,1,0,2,2,3],
    "Arc Warden": [1,1,0,3,3,1], "Axe": [3,3,3,1,0,0], "Bane": [3,1,0,2,0,1], "Batrider": [3,1,3,2,0,2],
    "Beastmaster": [2,2,3,1,3,0], "Bloodseeker": [2,1,2,2,1,1], "Bounty Hunter": [1,1,1,2,0,3], "Brewmaster": [2,3,3,2,1,2],
    "Bristleback": [0,3,1,2,1,0], "Broodmother": [1,2,1,2,3,2], "Centaur Warrunner": [3,3,3,1,1,1], "Chaos Knight": [2,3,2,3,1,1],
    "Chen": [1,1,1,1,3,0], "Clinkz": [0,1,1,3,3,2], "Clockwerk": [3,2,3,1,0,1], "Crystal Maiden": [3,0,1,2,0,0],
    "Dark Seer": [1,2,2,1,1,2], "Dark Willow": [3,1,1,3,0,2], "Dawnbreaker": [2,3,2,2,1,1], "Dazzle": [1,1,0,2,1,1],
    "Death Prophet": [1,2,1,2,3,1], "Disruptor": [3,0,1,2,0,0], "Doom": [2,3,2,2,0,1], "Dragon Knight": [3,3,2,2,2,0],
    "Drow Ranger": [1,0,0,3,2,1], "Earth Spirit": [3,2,3,1,0,2], "Earthshaker": [3,1,3,2,0,1], "Elder Titan": [2,2,2,2,1,0],
    "Ember Spirit": [1,1,2,2,0,3], "Enchantress": [1,1,1,2,2,1], "Enigma": [3,1,2,1,3,0], "Faceless Void": [3,2,3,2,1,2],
    "Grimstroke": [2,0,1,2,0,1], "Gyrocopter": [1,1,1,3,1,1], "Hoodwink": [2,0,1,3,0,2], "Huskar": [0,3,1,3,1,0],
    "Invoker": [2,1,2,3,1,2], "Io": [1,1,1,1,0,2], "Jakiro": [2,1,1,2,2,0], "Juggernaut": [0,1,1,2,3,2],
    "Keeper of the Light": [1,0,1,3,1,2], "Kez": [1,1,2,3,1,3], "Kunkka": [3,2,3,2,1,1], "Legion Commander": [2,3,2,2,1,1],
    "Leshrac": [1,1,1,3,3,1], "Lich": [2,0,1,3,0,0], "Lifestealer": [1,3,0,2,1,1], "Lina": [2,0,1,3,1,1],
    "Lion": [3,0,2,3,0,0], "Lone Druid": [1,2,1,2,3,1], "Luna": [1,1,1,2,3,1], "Lycan": [0,2,3,2,3,1],
    "Magnus": [3,2,3,1,0,1], "Marci": [2,2,2,2,0,2], "Mars": [3,3,3,1,1,1], "Medusa": [1,3,0,2,2,0],
    "Meepo": [2,2,1,3,2,2], "Mirana": [2,0,1,2,1,2], "Monkey King": [2,1,2,2,1,2], "Morphling": [1,1,1,3,1,3],
    "Muerta": [1,1,0,3,1,0], "Naga Siren": [2,2,1,1,3,2], "Nature's Prophet": [1,1,1,2,3,3], "Necrophos": [1,2,0,3,1,1],
    "Night Stalker": [2,2,3,2,0,2], "Nyx Assassin": [3,0,2,3,0,2], "Ogre Magi": [2,3,1,2,1,0], "Omniknight": [1,2,1,2,0,0],
    "Oracle": [2,0,0,2,0,1], "Outworld Destroyer": [2,1,1,3,1,1], "Pangolier": [2,1,3,2,0,3], "Phantom Assassin": [0,1,1,3,0,2],
    "Phantom Lancer": [1,1,1,2,1,3], "Phoenix": [2,2,2,3,0,2], "Primal Beast": [2,3,3,2,0,2], "Puck": [2,1,3,2,0,3],
    "Pudge": [2,3,2,2,0,1], "Pugna": [1,0,1,3,3,1], "Queen of Pain": [1,0,1,3,0,3], "Razor": [1,2,2,2,1,1],
    "Riki": [2,1,1,3,0,3], "Ringmaster": [3,1,1,2,0,1], "Rubick": [2,0,1,2,0,1], "Sand King": [3,2,3,2,1,2],
    "Shadow Demon": [2,0,1,1,0,1], "Shadow Fiend": [1,0,1,3,2,1], "Shadow Shaman": [3,1,1,2,3,0], "Silencer": [2,0,0,2,0,0],
    "Skywrath Mage": [1,0,0,3,0,0], "Slardar": [3,2,3,2,0,1], "Slark": [1,2,1,1,0,3], "Snapfire": [2,1,1,3,1,1],
    "Sniper": [1,0,0,3,2,1], "Spectre": [1,3,1,2,0,2], "Spirit Breaker": [3,2,3,1,0,2], "Storm Spirit": [1,1,3,3,0,3],
    "Sven": [2,2,2,3,2,1], "Techies": [2,1,1,3,1,2], "Templar Assassin": [1,1,1,3,2,2], "Terrorblade": [0,1,1,2,3,2],
    "Tidehunter": [3,3,3,1,1,0], "Timbersaw": [1,3,1,3,1,2], "Tinker": [1,1,2,3,0,2], "Tiny": [3,2,3,3,2,1],
    "Treant Protector": [3,2,2,1,1,1], "Troll Warlord": [1,2,1,2,3,1], "Tusk": [3,1,2,2,1,2], "Underlord": [2,3,1,1,2,0],
    "Undying": [2,3,1,1,0,0], "Ursa": [1,2,1,3,1,1], "Vengeful Spirit": [3,1,2,2,1,1], "Venomancer": [1,1,1,2,1,1],
    "Viper": [2,2,0,3,1,0], "Visage": [2,2,1,2,3,1], "Void Spirit": [2,1,3,2,0,3], "Warlock": [2,1,1,2,1,0],
    "Weaver": [1,1,1,2,1,3], "Windranger": [2,1,1,3,1,3], "Winter Wyvern": [3,1,1,2,1,2], "Witch Doctor": [2,1,1,3,0,0],
    "Wraith King": [2,3,1,2,2,1], "Zeus": [1,0,0,3,0,0], "Largo": [1,3,2,1,0,1]
}

# --- ПОЛНАЯ КАРТА ПОЗИЦИЙ ---
HERO_POSITIONS = {
    "Anti-Mage": [1], "Arc Warden": [1, 2], "Bloodseeker": [1, 2], "Chaos Knight": [1],
    "Clinkz": [1, 2], "Drow Ranger": [1], "Faceless Void": [1], "Gyrocopter": [1],
    "Juggernaut": [1], "Lifestealer": [1], "Luna": [1], "Medusa": [1], "Meepo": [1, 2],
    "Morphling": [1, 2], "Muerta": [1], "Naga Siren": [1], "Phantom Assassin": [1],
    "Phantom Lancer": [1], "Razor": [1, 2, 3], "Riki": [1], "Slark": [1], "Spectre": [1],
    "Sven": [1], "Templar Assassin": [1, 2], "Terrorblade": [1], "Troll Warlord": [1],
    "Ursa": [1], "Weaver": [1], "Wraith King": [1, 3], "Lone Druid": [1, 2, 3], "Monkey King": [1, 2],
    "Ember Spirit": [2], "Invoker": [2], "Kunkka": [2, 3], "Leshrac": [2], "Lina": [2],
    "Necrophos": [2, 3], "Outworld Destroyer": [2], "Pangolier": [2, 3], "Puck": [2],
    "Queen of Pain": [2], "Shadow Fiend": [1, 2], "Storm Spirit": [2], "Tinker": [2],
    "Void Spirit": [2], "Zeus": [2], "Sniper": [1, 2], "Batrider": [2, 3], "Primal Beast": [2, 3],
    "Axe": [3], "Beastmaster": [3], "Brewmaster": [3], "Bristleback": [3], "Centaur Warrunner": [3],
    "Dark Seer": [3], "Dawnbreaker": [3, 4], "Doom": [3], "Dragon Knight": [2, 3], "Enigma": [3, 4],
    "Legion Commander": [3], "Lycan": [3], "Magnus": [2, 3], "Mars": [3], "Night Stalker": [3],
    "Slardar": [3], "Tidehunter": [3], "Timbersaw": [2, 3], "Underlord": [3], "Viper": [2, 3],
    "Visage": [2, 3], "Sand King": [3], "Largo": [3, 4, 5],
    "Ancient Apparition": [4, 5], "Bane": [5], "Bounty Hunter": [4], "Chen": [5], "Clockwerk": [4],
    "Crystal Maiden": [5], "Dark Willow": [4, 5], "Dazzle": [5], "Disruptor": [5], "Earth Spirit": [4],
    "Earthshaker": [4], "Elder Titan": [4, 5], "Enchantress": [4, 5], "Grimstroke": [4, 5],
    "Hoodwink": [4], "Io": [4, 5], "Jakiro": [5], "Keeper of the Light": [4], "Lich": [5],
    "Lion": [4, 5], "Mirana": [4], "Nyx Assassin": [4], "Ogre Magi": [5], "Omniknight": [5],
    "Oracle": [5], "Pugna": [4, 5], "Rubick": [4], "Shadow Demon": [5], "Shadow Shaman": [5],
    "Silencer": [5], "Skywrath Mage": [4, 5], "Snapfire": [4], "Spirit Breaker": [4],
    "Techies": [4], "Treant Protector": [4, 5], "Tusk": [4], "Undying": [5], "Vengeful Spirit": [4, 5],
    "Venomancer": [4, 5], "Warlock": [5], "Winter Wyvern": [5], "Witch Doctor": [5], "Pudge": [4, 5]
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

        # 1. Анализ баланса команды
        team_tags = [0, 0, 0, 0, 0, 0]
        for ally in payload.my_team.values():
            if ally and ally in HERO_TAGS:
                for i in range(6): team_tags[i] += HERO_TAGS[ally][i]

        # 2. Immortal Winrate
        base_wr = {}
        for hs in h_stats:
            p, w = hs.get("8_pick", 0), hs.get("8_win", 0)
            name = hs.get("localized_name")
            if name: base_wr[name] = (w/p*100) if p > 35 else (hs.get("7_win", 1)/hs.get("7_pick", 1)*100)

        # 3. Анализ контрпиков
        enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
        enemies_results = await asyncio.gather(*(get_matchups_data(eid) for eid in enemy_ids))

        hero_final_stats = []
        for h in h_list:
            name = h["localized_name"]
            if name.lower() in picked: continue
            
            enemy_advs = []
            is_hard_countered = False
            for m_list in enemies_results:
                for m in m_list:
                    if m["hero_id"] == h["id"] and m["games_played"] > 10:
                        adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                        if adv < -6.5: is_hard_countered = True
                        enemy_advs.append(adv if adv > 0 else adv * 2.5)

            avg_adv = sum(enemy_advs) / len(enemy_advs) if enemy_advs else 0
            
            # 4. Бонус за баланс состава
            role_bonus = 0
            if name in HERO_TAGS:
                h_t = HERO_TAGS[name]
                if team_tags[0] < 5: role_bonus += h_t[0] * 1.5 
                if team_tags[1] < 4: role_bonus += h_t[1] * 2.5 
                if team_tags[2] < 4: role_bonus += h_t[2] * 2.0 
                if team_tags[4] < 3: role_bonus += h_t[4] * 1.5 

            final_wr = base_wr.get(name, 50) + avg_adv + role_bonus
            if is_hard_countered: final_wr -= 12.0
            
            final_wr = max(5.0, min(95.0, final_wr))
            hero_final_stats.append({"id": h["id"], "name": name, "img": img_map.get(name), "winrate": round(final_wr, 1), "advantage": round(avg_adv, 1)})

        # 5. Результаты
        fav_ids = get_db_favs(payload.user_id) if payload.user_id else []
        final_results = []
        for r_k, r_t in ROLES.items():
            if payload.my_team.get(r_k): continue
            pos = int(r_k[-1])
            eligible = [c for c in hero_final_stats if pos in HERO_POSITIONS.get(c["name"], [])]
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
