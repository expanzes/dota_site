import asyncio, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection, get_favorites
from routers.constants import HERO_TAGS, HERO_POSITIONS, ILLUSION_HERO_NAMES, ILLUSION_KILLERS

router = APIRouter()
MATCHUP_CACHE = {}

ROLES = {"pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"}

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
        h_list, h_stats = h_res.json(), s_res.json()
        
        name_to_id = {h["localized_name"].lower(): h["id"] for h in h_list}
        img_map = {h["localized_name"]: f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png" for h in h_list}
        picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}

        team_tags = [0] * 6
        for ally in payload.my_team.values():
            if ally in HERO_TAGS:
                for i in range(6): team_tags[i] += HERO_TAGS[ally][i]

        base_wr = {hs["localized_name"]: (hs.get("8_win", 0)/hs.get("8_pick", 1)*100) if hs.get("8_pick", 0) > 35 else (hs.get("7_win", 1)/hs.get("7_pick", 1)*100) for hs in h_stats if "localized_name" in hs}

        enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
        enemies_results = await asyncio.gather(*(get_matchups_data(eid) for eid in enemy_ids))
        enemy_has_killer = any(en.title() in ILLUSION_KILLERS for en in payload.enemy_team)

        hero_final_stats = []
        for h in h_list:
            name = h["localized_name"]
            if name.lower() in picked: continue
            
            advs, worst = [], 0
            for m_list in enemies_results:
                for m in m_list:
                    if m["hero_id"] == h["id"] and m["games_played"] > 10:
                        adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                        score = adv * 3.5 if adv < 0 else adv
                        advs.append(score)
                        if score < worst: worst = score

            avg_adv = sum(advs)/len(advs) if advs else 0
            counter_rating = (avg_adv * 0.4) + (worst * 0.6)
            
            pnlty = -25.0 if name in ILLUSION_HERO_NAMES and enemy_has_killer else 0
            role_bn = 0
            if name in HERO_TAGS:
                t = HERO_TAGS[name]
                if team_tags[0] < 5: role_bn += t[0] * 1.5 
                if team_tags[1] < 4: role_bn += t[1] * 2.5 
                if team_tags[2] < 4: role_bn += t[2] * 2.0 
                if team_tags[4] < 3: role_bn += t[4] * 1.5 

            final_wr = max(5.0, min(95.0, base_wr.get(name, 50) + counter_rating + role_bn + pnlty))
            hero_final_stats.append({"id": h["id"], "name": name, "img": img_map.get(name), "winrate": round(final_wr, 1), "advantage": round(counter_rating, 1)})

        fav_ids = []
        if payload.user_id:
            fav_data = await get_favorites(payload.user_id)
            fav_ids = fav_data["favorite_ids"]
            
        final_results = []
        for r_k, r_t in ROLES.items():
            if payload.my_team.get(r_k): continue
            pos = int(r_k[-1])
            eligible = sorted([c for c in hero_final_stats if pos in HERO_POSITIONS.get(c["name"], [])], key=lambda x: -x["winrate"])
            
            used = set()
            def pick(lst):
                for c in lst:
                    if c["id"] not in used:
                        used.add(c["id"]); return c
                return None

            final_results.append({
                "role": r_t, 
                "data": {
                    "top_favorite": pick([c for c in eligible if c["id"] in fav_ids]), 
                    "top_winrate": pick(eligible), 
                    "others": [pick(eligible) for _ in range(3)]
                }
            })
        return {"results": final_results}
    except Exception as e:
        raise HTTPException(500, str(e))
