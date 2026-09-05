import asyncio, httpx, time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection, get_favorites_db
from routers.constants import HERO_TAGS, HERO_POSITIONS, ILLUSION_HERO_NAMES, ILLUSION_KILLERS, HERO_ALIASES, HERO_COMBOS

router = APIRouter()

CACHE = {
    "heroes": [],
    "last_update": 0
}
MATCHUP_CACHE = {}

ROLES = {"pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"}

async def get_heroes_list():
    now = time.time()
    if CACHE["heroes"] and (now - CACHE["last_update"] < 3600):
        return CACHE["heroes"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://api.opendota.com/api/heroes")
            if r.status_code == 200:
                data = r.json()
                processed_heroes = []
                for h in data:
                    name = h["localized_name"]
                    img_name = h['name'].replace('npc_dota_hero_', '')
                    processed_heroes.append({
                        "id": h["id"],
                        "name": name,
                        "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{img_name}.png",
                        "aliases": HERO_ALIASES.get(name, [])
                    })
                CACHE["heroes"] = processed_heroes
                CACHE["last_update"] = now
                return CACHE["heroes"]
    except:
        return CACHE["heroes"] if CACHE["heroes"] else []

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

def predict_enemy_roles(enemy_names):
    assigned = {}
    unassigned = [h.title() for h in enemy_names]
    unassigned.sort(key=lambda h: len(HERO_POSITIONS.get(h, [1,2,3,4,5])))
    
    for h in unassigned:
        placed = False
        for r in HERO_POSITIONS.get(h, [1,2,3,4,5]):
            if r not in assigned.values():
                assigned[h] = r
                placed = True
                break
        if not placed:
            for r in [1,2,3,4,5]:
                if r not in assigned.values():
                    assigned[h] = r
                    break
    return assigned

class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

@router.get("/heroes")
async def heroes_endpoint():
    return await get_heroes_list()

@router.post("/analyze")
async def analyze_perfect(payload: DraftRequest):
    try:
        h_list = await get_heroes_list()
        async with httpx.AsyncClient() as c:
            s_res = await c.get("https://api.opendota.com/api/heroStats")
            h_stats = s_res.json()
        
        name_to_id = {h["name"].lower(): h["id"] for h in h_list}
        img_map = {h["name"]: h["img"] for h in h_list}
        picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
        picked_allies = [v.title() for v in payload.my_team.values() if v]

        team_tags = [0] * 8
        for ally in picked_allies:
            if ally in HERO_TAGS:
                for i in range(8): team_tags[i] += HERO_TAGS[ally][i]
        
        current_team_greed = team_tags[6]

        base_wr = {hs["localized_name"]: (hs.get("8_win", 0)/hs.get("8_pick", 1)*100) if hs.get("8_pick", 0) > 35 else (hs.get("7_win", 1)/hs.get("7_pick", 1)*100) for hs in h_stats if "localized_name" in hs}

        enemy_roles = predict_enemy_roles(payload.enemy_team)
        enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
        enemies_results = await asyncio.gather(*(get_matchups_data(eid) for eid in enemy_ids))
        enemy_has_killer = any(en.title() in ILLUSION_KILLERS for en in payload.enemy_team)

        adv_matrix = {}
        for i, m_list in enumerate(enemies_results):
            en_id = enemy_ids[i]
            for m in m_list:
                h_id = m["hero_id"]
                if h_id not in adv_matrix: adv_matrix[h_id] = {}
                if m["games_played"] > 10:
                    adv_matrix[h_id][en_id] = (1 - (m["wins"] / m["games_played"])) * 100

        fav_ids = []
        if payload.user_id:
            fav_data = await get_favorites_db(payload.user_id)
            fav_ids = fav_data["favorite_ids"]
            
        used_recommendations = set()
        final_results = []

        for r_k, r_t in ROLES.items():
            if payload.my_team.get(r_k): continue
            pos = int(r_k[-1])
            
            lane_enemies = []
            if pos == 1: lane_enemies = [3, 4]
            elif pos == 2: lane_enemies = [2, 4]
            elif pos == 3: lane_enemies = [1, 5]
            elif pos == 4: lane_enemies = [1, 5]
            elif pos == 5: lane_enemies = [3, 4]

            role_candidates = []
            for h in h_list:
                name = h["name"]
                if name.lower() in picked: continue
                if pos not in HERO_POSITIONS.get(name, []): continue

                advs, worst = [], 0
                for en_id, en_name in zip(enemy_ids, payload.enemy_team):
                    en_pos = enemy_roles.get(en_name.title(), 0)
                    weight = 1.5 if en_pos in lane_enemies else 1.0
                    
                    raw_wr_vs_en = adv_matrix.get(h["id"], {}).get(en_id)
                    if raw_wr_vs_en:
                        adv = raw_wr_vs_en - base_wr.get(name, 50)
                        score = adv * 3.5 if adv < 0 else adv
                        score *= weight
                        advs.append(score)
                        if score < worst: worst = score

                avg_adv = sum(advs)/len(advs) if advs else 0
                counter_rating = (avg_adv * 0.4) + (worst * 0.6)
                
                role_bn = 0
                greed_penalty = 0
                combo_bonus = 0
                pnlty = -25.0 if name in ILLUSION_HERO_NAMES and enemy_has_killer else 0

                if name in HERO_TAGS:
                    t = HERO_TAGS[name]
                    if team_tags[0] < 5: role_bn += t[0] * 1.5 
                    if team_tags[1] < 4: role_bn += t[1] * 2.5 
                    if team_tags[2] < 4: role_bn += t[2] * 2.0 
                    if team_tags[4] < 3: role_bn += t[4] * 1.5 
                    
                    cand_greed = t[6]
                    if current_team_greed + cand_greed > 7:
                        greed_penalty = -((current_team_greed + cand_greed - 7) * 3.0)

                for ally in picked_allies:
                    if name in HERO_COMBOS.get(ally, []) or ally in HERO_COMBOS.get(name, []):
                        combo_bonus += 4.0

                # ЛОГИКА ЛЮБИМЫХ ГЕРОЕВ
                is_fav = h["id"] in fav_ids
                fav_bonus = 0
                if is_fav and counter_rating >= -2.0:
                    fav_bonus = 3.5 # Бонус дается только если герой не законтрен

                final_wr = max(5.0, min(95.0, base_wr.get(name, 50) + counter_rating + role_bn + greed_penalty + combo_bonus + pnlty + fav_bonus))
                
                role_candidates.append({
                    "id": h["id"], "name": name, "img": img_map.get(name), 
                    "winrate": round(final_wr, 1), "advantage": round(counter_rating, 1),
                    "is_favorite": is_fav
                })

            # ЖЕСТКИЙ ФИЛЬТР (отсекаем все, что ниже 48% винрейта)
            filtered_candidates = [c for c in role_candidates if c["winrate"] >= 48.0]
            if len(filtered_candidates) < 5:
                filtered_candidates = role_candidates # Если пик совсем плохой, возвращаем весь список

            filtered_candidates.sort(key=lambda x: -x["winrate"])
            
            top_5 = []
            for c in filtered_candidates:
                if c["id"] not in used_recommendations:
                    used_recommendations.add(c["id"])
                    top_5.append(c)
                    if len(top_5) == 5:
                        break

            # ТЕПЕРЬ СЕРВЕР ОТДАЕТ ПРОСТО МАССИВ ИЗ 5 ГЕРОЕВ
            final_results.append({
                "role": r_t, 
                "candidates": top_5
            })
            
        return {"results": final_results}
    except Exception as e: raise HTTPException(500, str(e))
