import asyncio, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from routers.auth import get_db_connection

router = APIRouter()

# Кэш матчапов
MATCHUP_CACHE = {}

ROLES = {
    "pos1": "Поз 1 (Керри)", "pos2": "Поз 2 (Мид)", "pos3": "Поз 3 (Тройка)", 
    "pos4": "Поз 4 (Четверка)", "pos5": "Поз 5 (Пятерка)"
}

# Актуальная мета позиций (включая Largo и Slardar как разных героев)
HERO_POSITIONS = {
    "Largo": [3, 4, 5], "Slardar": [3], "Anti-Mage": [1], "Axe": [3], 
    "Invoker": [2], "Pudge": [1, 3, 4, 5], "Naga Siren": [1], "Monkey King": [1, 2],
    "Ember Spirit": [2], "Juggernaut": [1], "Slark": [1], "Tidehunter": [3],
    "Ancient Apparition": [4, 5], "Bloodseeker": [1, 2], "Bane": [5], "Crystal Maiden": [5],
    "Shadow Fiend": [1, 2], "Lone Druid": [1, 2, 3], "Dark Willow": [4, 5], "Disruptor": [5],
    "Ember Spirit": [2], "Io": [4, 5], "Hoodwink": [4], "Mirana": [4],
    # Если героя нет в списке, система позволит ему быть на любой позиции, 
    # но для точности лучше расширять этот список.
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
            h_res, s_res = await asyncio.gather(
                c.get("https://api.opendota.com/api/heroes"), 
                c.get("https://api.opendota.com/api/heroStats")
            )
        
        h_list = h_res.json()
        h_stats = s_res.json()
        
        # Словари для поиска по Localized Name (гарантия разделения Largo и Slardar)
        id_to_name = {h["id"]: h["localized_name"] for h in h_list}
        name_to_id = {h["localized_name"].lower(): h["id"] for h in h_list}
        img_map = {h["localized_name"]: f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{h['name'].replace('npc_dota_hero_', '')}.png" for h in h_list}
        
        picked = {v.lower() for v in payload.my_team.values() if v} | {n.lower() for n in payload.enemy_team}
        
        # 1. Определение базового винрейта (Divine/Immortal)
        base_wr = {}
        for hs in h_stats:
            name = hs.get("localized_name")
            p = hs.get("8_pick", 0) # Immortal rank
            w = hs.get("8_win", 0)
            if name:
                base_wr[name] = (w/p*100) if p > 30 else (hs.get("7_win", 1)/hs.get("7_pick", 1)*100)

        # 2. Сбор данных о матчапах
        enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
        enemies_matchups = await asyncio.gather(*(get_matchups_data(eid) for eid in enemy_ids))

        hero_final_stats = []
        for h in h_list:
            name = h["localized_name"]
            if name.lower() in picked: continue
            
            # Считаем преимущество (Advantage) против каждого врага
            enemy_advs = []
            is_hard_countered = False
            
            for m_list in enemies_matchups:
                for m in m_list:
                    if m["hero_id"] == h["id"] and m["games_played"] > 10:
                        # Advantage = (WR в матчапе) - (Средний WR)
                        adv = (100 - (m["wins"]/m["games_played"]*100)) - base_wr.get(name, 50)
                        
                        # Детектор хард-контрпика
                        if adv < -6.5: is_hard_countered = True
                        
                        # Взвешиваем преимущество (отрицательное важнее для выживаемости)
                        enemy_advs.append(adv if adv > 0 else adv * 2.0)

            # МАТЕМАТИЧЕСКИЙ ФИКС: Берем СРЕДНЕЕ преимущество, а не сумму
            avg_adv = sum(enemy_advs) / len(enemy_advs) if enemy_advs else 0
            
            final_wr = base_wr.get(name, 50) + avg_adv
            
            # Штраф за "неиграбельность" против хард-контрпика
            if is_hard_countered: final_wr -= 10.0
            
            # Жесткий программный лимит винрейта
            final_wr = max(5.0, min(95.0, final_wr))

            hero_final_stats.append({
                "id": h["id"], "name": name, "img": img_map.get(name),
                "winrate": round(final_wr, 1),
                "advantage": round(avg_adv, 1)
            })

        # 3. Подбор по ролям
        fav_ids = get_db_favs(payload.user_id) if payload.user_id else []
        final_results = []
        for r_k, r_t in ROLES.items():
            if payload.my_team.get(r_k): continue
            
            pos = int(r_k[-1])
            # Фильтрация по мете позиций
            eligible = [c for c in hero_final_stats if pos in HERO_POSITIONS.get(c["name"], [1,2,3,4,5])]
            ranked = sorted(eligible, key=lambda x: -x["winrate"])
            
            used = set()
            def pick_hero(lst):
                for c in lst:
                    if c["id"] not in used:
                        used.add(c["id"])
                        return c
                return None

            final_results.append({
                "role": r_t,
                "data": {
                    "top_favorite": pick_hero([c for c in ranked if c["id"] in fav_ids]),
                    "top_winrate": pick_hero(ranked),
                    "others": [pick_hero(ranked) for _ in range(3)]
                }
            })
        return {"results": final_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
