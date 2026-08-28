import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
import httpx
from routers.auth import get_db_connection, ensure_tables_exist

router = APIRouter()

HEROES_CACHE: List[dict] = []
HERO_STATS_CACHE: List[dict] = []
MATCHUP_CACHE: Dict[int, List[dict]] = {}

MIN_GAMES_FOR_RANK = 50      # минимум игр героя в паблике, чтобы считать его винрейт надёжным
MIN_GAMES_FOR_MATCHUP = 30   # минимум игр в конкретном противостоянии, иначе выборка ненадёжна
OTHERS_COUNT = 3             # сколько доп. карточек показывать под топ-плашками

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

# ---------------------------------------------------------------------------
# Соответствие героев ролям (позициям 1-5).
#
# OpenDota не отдаёт готовые данные "герой играет на позиции 1-5" — это
# игровая мета, которой нет в их API как отдельного поля. Поэтому таблица
# ниже курируется вручную на основе актуальной меты. Список охватывает
# практически весь ростер героев; если герой не найден в таблице —
# считаем его подходящим для любой позиции (чтобы не ломать выдачу на
# только что вышедших героях, которых мы не успели вписать).
# ---------------------------------------------------------------------------

HERO_POSITIONS: Dict[str, List[int]] = {
    "Abaddon": [3, 4, 5],
    "Alchemist": [1, 3],
    "Ancient Apparition": [4, 5],
    "Anti-Mage": [1],
    "Arc Warden": [1, 2],
    "Axe": [3],
    "Bane": [4, 5],
    "Batrider": [2, 3],
    "Beastmaster": [3],
    "Bloodseeker": [1, 2],
    "Bounty Hunter": [4],
    "Brewmaster": [3],
    "Bristleback": [3],
    "Broodmother": [1, 2, 3],
    "Centaur Warrunner": [3],
    "Chaos Knight": [1],
    "Chen": [5],
    "Clinkz": [1, 2, 3],
    "Clockwerk": [3, 4],
    "Crystal Maiden": [5],
    "Dark Seer": [3],
    "Dark Willow": [4, 5],
    "Dawnbreaker": [3, 4],
    "Dazzle": [4, 5],
    "Death Prophet": [2, 3],
    "Disruptor": [5],
    "Doom": [3],
    "Dragon Knight": [2, 3],
    "Drow Ranger": [1],
    "Earth Spirit": [3, 4],
    "Earthshaker": [3, 4],
    "Elder Titan": [3, 4],
    "Ember Spirit": [2],
    "Enchantress": [4, 5],
    "Enigma": [3, 4],
    "Faceless Void": [1],
    "Grimstroke": [4, 5],
    "Gyrocopter": [1, 2],
    "Hoodwink": [4, 5],
    "Huskar": [1, 2],
    "Invoker": [2],
    "Io": [5],
    "Jakiro": [4, 5],
    "Juggernaut": [1],
    "Keeper of the Light": [4, 5],
    "Kez": [1, 2],
    "Kunkka": [2, 3],
    "Legion Commander": [3],
    "Leshrac": [2, 3],
    "Lich": [4, 5],
    "Lifestealer": [1],
    "Lina": [2, 4],
    "Lion": [4, 5],
    "Luna": [1],
    "Lycan": [1, 3],
    "Magnus": [2, 3],
    "Marci": [3, 4],
    "Mars": [3],
    "Medusa": [1],
    "Meepo": [1, 2],
    "Mirana": [2, 4],
    "Monkey King": [1, 2, 3],
    "Morphling": [1],
    "Muerta": [2, 5],
    "Naga Siren": [1],
    "Nature's Prophet": [2, 3],
    "Necrophos": [2, 3],
    "Night Stalker": [3],
    "Nyx Assassin": [3, 4],
    "Ogre Magi": [4, 5],
    "Omniknight": [4, 5],
    "Oracle": [4, 5],
    "Outworld Destroyer": [2, 3],
    "Pangolier": [2, 3],
    "Phantom Assassin": [1],
    "Phantom Lancer": [1],
    "Primal Beast": [3, 4],
    "Puck": [2],
    "Pudge": [3, 4],
    "Pugna": [2, 5],
    "Queen of Pain": [2],
    "Razor": [1, 2, 3],
    "Riki": [1, 3, 4],
    "Ringmaster": [4, 5],
    "Rubick": [4, 5],
    "Sand King": [3],
    "Shadow Demon": [4, 5],
    "Shadow Fiend": [2],
    "Shadow Shaman": [4, 5],
    "Silencer": [4, 5],
    "Skywrath Mage": [4, 5],
    "Slardar": [3],
    "Slark": [1],
    "Snapfire": [4, 5],
    "Sniper": [1, 2],
    "Spectre": [1],
    "Spirit Breaker": [3, 4],
    "Storm Spirit": [2],
    "Sven": [1, 3],
    "Techies": [4, 5],
    "Templar Assassin": [2],
    "Terrorblade": [1],
    "Tidehunter": [3],
    "Timbersaw": [3],
    "Tinker": [2],
    "Tiny": [1, 3],
    "Treant Protector": [4, 5],
    "Troll Warlord": [1],
    "Tusk": [3, 4],
    "Underlord": [3],
    "Undying": [4, 5],
    "Ursa": [1, 2, 3],
    "Vengeful Spirit": [4, 5],
    "Venomancer": [3, 4],
    "Viper": [2, 3],
    "Visage": [4, 5],
    "Void Spirit": [2, 3],
    "Warlock": [4, 5],
    "Weaver": [1, 2, 4],
    "Windranger": [2, 4],
    "Winter Wyvern": [4, 5],
    "Witch Doctor": [4, 5],
    "Wraith King": [1, 3],
    "Zeus": [2, 4],
}


def positions_for_hero(hero_name: str) -> List[int]:
    """Позиции, для которых подходит герой. Если героя нет в таблице —
    считаем подходящим для любой позиции, чтобы не терять новых героев."""
    return HERO_POSITIONS.get(hero_name, [1, 2, 3, 4, 5])


# ---------------------------------------------------------------------------
# Загрузка и кэширование данных с OpenDota
# ---------------------------------------------------------------------------

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
    return FALLBACK_HEROES


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


async def get_matchups(hero_id: int) -> List[dict]:
    """Матчапы конкретного героя против всех остальных (кэшируется по ID)."""
    if hero_id in MATCHUP_CACHE:
        return MATCHUP_CACHE[hero_id]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://api.opendota.com/api/heroes/{hero_id}/matchups")
            if response.status_code == 200:
                data = response.json()
                MATCHUP_CACHE[hero_id] = data
                return data
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


@router.get("/heroes")
async def get_heroes():
    return await get_heroes_cache()


# ---------------------------------------------------------------------------
# Модели запроса/кандидата
# ---------------------------------------------------------------------------

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


def build_recommendation_pool_for_position(
    all_candidates: List[dict],
    pos_num: int,
    favorite_ids: List[int],
) -> dict:
    """Строит рекомендации (пул/винрейт/остальные) для конкретной позиции,
    отфильтровав кандидатов заранее по тому, подходят ли они на эту роль."""

    eligible = [c for c in all_candidates if pos_num in positions_for_hero(c["name"])]
    # На случай если фильтр по позиции внезапно вырезал всех кандидатов
    # (не должно происходить при полной таблице позиций) — не оставляем
    # пользователя без рекомендаций вообще.
    pool_source = eligible if eligible else all_candidates

    reliable = [c for c in pool_source if c["games"] >= MIN_GAMES_FOR_RANK]
    pool = reliable if reliable else pool_source

    ranked_by_winrate = sorted(pool, key=lambda c: -c["winrate"])

    used_ids = set()

    def take_first(sorted_list):
        for c in sorted_list:
            if c["id"] not in used_ids:
                used_ids.add(c["id"])
                return c
        return None

    top_winrate = take_first(ranked_by_winrate)

    top_favorite = None
    if favorite_ids:
        favorite_candidates = [c for c in ranked_by_winrate if c["id"] in favorite_ids]
        top_favorite = take_first(favorite_candidates)

    others = [c for c in ranked_by_winrate if c["id"] not in used_ids][:OTHERS_COUNT]

    return {
        "top_favorite": format_hero(top_favorite),
        "top_winrate": format_hero(top_winrate),
        "others": [format_hero(c) for c in others],
    }


# ---------------------------------------------------------------------------
# Основной алгоритм подбора
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze_draft(payload: DraftRequest):
    heroes_list = await get_heroes_cache()
    hero_stats = await get_hero_stats_cache()

    name_to_id = {h["name"].lower(): h["id"] for h in heroes_list}
    id_to_name = {h["id"]: h["name"] for h in heroes_list}

    # Уже выбранные герои (своя команда + враги) — исключаем из кандидатов.
    ally_names_lower = {v.lower() for v in payload.my_team.values() if v}
    enemy_names_lower = {n.lower() for n in payload.enemy_team}
    picked_names_lower = ally_names_lower | enemy_names_lower

    # --- Базовый (общий паблик) винрейт и число игр по каждому герою ---
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

    # --- Контрпик-очки против выбранных героев врага ---
    enemy_ids = [name_to_id[n.lower()] for n in payload.enemy_team if n.lower() in name_to_id]
    matchup_results = await asyncio.gather(*(get_matchups(eid) for eid in enemy_ids))

    counter_score: Dict[str, List[float]] = {}  # candidate_name -> [взвеш. сумма винрейта, суммарный вес]
    for matchups in matchup_results:
        for m in matchups:
            games = m.get("games_played", 0)
            if games < MIN_GAMES_FOR_MATCHUP:
                continue
            candidate_name = id_to_name.get(m.get("hero_id"))
            if not candidate_name:
                continue
            enemy_wins = m.get("wins", 0)
            # m["wins"] — победы ВРАГА в этом противостоянии, поэтому винрейт
            # кандидата против конкретного врага — это обратная величина.
            candidate_wr_vs_this_enemy = 100 - (enemy_wins / games * 100)
            entry = counter_score.setdefault(candidate_name, [0.0, 0.0])
            entry[0] += candidate_wr_vs_this_enemy * games
            entry[1] += games

    # --- Итоговая оценка кандидатов (общая, без учёта позиции) ---
    all_candidates = []
    for h in heroes_list:
        name = h["name"]
        if name.lower() in picked_names_lower:
            continue

        base = base_winrate.get(name, 50)
        games = base_games.get(name, 0)

        if name in counter_score and counter_score[name][1] > 0:
            counter_wr = counter_score[name][0] / counter_score[name][1]
            # Чем больше выбрано вражеских героев, тем больше вес контрпика
            # в итоговой оценке — против пустого драфта врага контрпик не считаем.
            enemy_weight = min(len(enemy_ids) / 5, 1.0) * 0.7
            draft_winrate = counter_wr * enemy_weight + base * (1 - enemy_weight)
        else:
            draft_winrate = base

        all_candidates.append({
            "id": h["id"],
            "name": name,
            "img": h["img"],
            "winrate": round(draft_winrate, 1),
            "games": games,
        })

    favorite_ids = get_user_favorite_ids(payload.user_id)

    # --- Для каждой незаполненной роли строим отдельный, отфильтрованный по позиции пул ---
    results = []
    for role_key, role_title in ROLES.items():
        if payload.my_team.get(role_key):
            continue
        pos_num = int(role_key[-1])
        recommendation_pool = build_recommendation_pool_for_position(
            all_candidates, pos_num, favorite_ids
        )
        results.append({"role": role_title, "data": recommendation_pool})

    return {"results": results}
