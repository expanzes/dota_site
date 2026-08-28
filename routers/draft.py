import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
import httpx
from routers.auth import get_db_connection, ensure_tables_exist

router = APIRouter()

HEROES_CACHE: List[dict] = []
HERO_STATS_CACHE: List[dict] = []

MIN_GAMES_FOR_RANK = 50      # мин. игр, чтобы попасть в основной топ по общему винрейту
MIN_GAMES_FOR_MATCHUP = 30   # мин. игр в конкретном матчапе, иначе выборка ненадёжна


async def get_heroes_cache() -> List[dict]:
    global HEROES_CACHE
    if HEROES_CACHE:
        return HEROES_CACHE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.opendota.com/api/heroes")
            if response.status_code == 200:
                data = response.json()
                HEROES_CACHE = [
                    {
                        "id": hero["id"],
                        "name": hero["localized_name"],
                        "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero['name'].replace('npc_dota_hero_', '')}.png",
                    }
                    for hero in data
                ]
                return HEROES_CACHE
    except Exception as e:
        print(f"Ошибка при запросе списка героев к OpenDota: {e}")

    return [
        {"id": 1, "name": "Anti-Mage", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png"},
        {"id": 14, "name": "Pudge", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/pudge.png"},
        {"id": 74, "name": "Invoker", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/invoker.png"},
    ]


@router.get("/heroes")
async def get_heroes():
    return await get_heroes_cache()


async def get_hero_stats_cache() -> List[dict]:
    global HERO_STATS_CACHE
    if HERO_STATS_CACHE:
        return HERO_STATS_CACHE
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.opendota.com/api/heroStats")
            if response.status_code == 200:
                HERO_STATS_CACHE = response.json()
                return HERO_STATS_CACHE
    except Exception as e:
        print(f"Ошибка при запросе heroStats к OpenDota: {e}")
    return []


async def fetch_matchups(hero_id: int) -> List[dict]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Ошибка при запросе matchups для героя {hero_id}: {e}")
    return []


def get_user_favorite_ids(user_id: Optional[str]) -> List[int]:
    if not user_id:
        return []
    try:
        ensure_tables_exist()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT favorite_ids FROM favorites WHERE user_id = %s;", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] else []
    except Exception as e:
        print(f"Ошибка при чтении избранного: {e}")
        return []


class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None


def format_hero(candidate: Optional[dict]) -> Optional[dict]:
    if not candidate:
        return None
    return {
        "name": candidate["name"],
        "winrate": candidate["winrate"],
        "games": candidate["games"],
        "img": candidate["img"],
    }


@router.post("/analyze")
async def analyze_draft(payload: DraftRequest):
    heroes_list = await get_heroes_cache()
    hero_stats = await get_hero_stats_cache()

    name_to_id = {h["name"].lower(): h["id"] for h in heroes_list}
    id_to_name = {h["id"]: h["name"] for h in heroes_list}

    picked_names_lower = {v.lower() for v in payload.my_team.values() if v}
    picked_names_lower |= {n.lower() for n in payload.enemy_team}

    # --- Базовый (общий) винрейт по паблик-статистике OpenDota ---
    base_winrate: Dict[str, float] = {}
    base_games: Dict[str, int] = {}
    for hs in hero_stats:
        name = hs.get("localized_name")
        if not name:
            continue
        total_pick = sum(hs.get(f"{i}_pick", 0) or 0 for i in range(1, 9))
        total_win = sum(hs.get(f"{i}_win", 0) or 0 for i in range(1, 9))
        base_winrate[name] = (total_win / total_pick * 100) if total_pick else 0
        base_games[name] = total_pick

    # --- Контрпики против выбранных героев врага ---
    enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
    matchup_results = await asyncio.gather(*(fetch_matchups(eid) for eid in enemy_ids))

    counter_score: Dict[str, List[float]] = {}  # name -> [weighted_sum, weight]
    for matchups in matchup_results:
        for m in matchups:
            games = m.get("games_played", 0)
            if games < MIN_GAMES_FOR_MATCHUP:
                continue
            opp_name = id_to_name.get(m.get("hero_id"))
            if not opp_name:
                continue
            enemy_wins = m.get("wins", 0)
            counter_wr = 100 - (enemy_wins / games * 100)  # винрейт opp_name против этого врага
            entry = counter_score.setdefault(opp_name, [0.0, 0.0])
            entry[0] += counter_wr * games
            entry[1] += games

    # --- Финальный скоринг кандидатов ---
    candidates = []
    for h in heroes_list:
        name = h["name"]
        if name.lower() in picked_names_lower:
            continue

        base = base_winrate.get(name, 50)
        games = base_games.get(name, 0)

        if name in counter_score and counter_score[name][1] > 0:
            counter_wr = counter_score[name][0] / counter_score[name][1]
            score = counter_wr * 0.7 + base * 0.3  # с врагами в приоритете контрпик
        else:
            score = base

        candidates.append({
            "id": h["id"],
            "name": name,
            "img": h["img"],
            "winrate": round(base, 1),
            "games": games,
            "score": score,
        })

    ranked = sorted(
        [c for c in candidates if c["games"] >= MIN_GAMES_FOR_RANK],
        key=lambda c: -c["score"],
    )
    if not ranked:
        ranked = sorted(candidates, key=lambda c: -c["score"])

    used_ids = set()

    def take(cands, key=lambda c: -c["score"]):
        pool = sorted((c for c in cands if c["id"] not in used_ids), key=key)
        if not pool:
            return None
        chosen = pool[0]
        used_ids.add(chosen["id"])
        return chosen

    top_winrate = take(ranked)
    top_games = take(ranked, key=lambda c: -c["games"])

    favorite_ids = get_user_favorite_ids(payload.user_id)
    top_favorite = None
    if favorite_ids:
        top_favorite = take([c for c in ranked if c["id"] in favorite_ids])

    others = [c for c in ranked if c["id"] not in used_ids][:6]

    recommendation_pool = {
        "top_favorite": format_hero(top_favorite),
        "top_winrate": format_hero(top_winrate),
        "top_games": format_hero(top_games),
        "others": [format_hero(c) for c in others],
    }

    roles = {
        "pos1": "Поз 1 (Керри)",
        "pos2": "Поз 2 (Мид)",
        "pos3": "Поз 3 (Тройка)",
        "pos4": "Поз 4 (Четверка)",
        "pos5": "Поз 5 (Пятерка)",
    }

    results = [
        {"role": role_title, "data": recommendation_pool}
        for role_key, role_title in roles.items()
        if not payload.my_team.get(role_key)
    ]

    return {"results": results}
