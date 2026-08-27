import json
import os
import urllib.request
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from pydantic import BaseModel

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

HERO_CACHE = {}


class MyTeam(BaseModel):
  pos1: str = ""
  pos2: str = ""
  pos3: str = ""
  pos4: str = ""
  pos5: str = ""


class DraftRequest(BaseModel):
  my_team: MyTeam
  enemy_team: list[str]


def get_opendota_heroes():
  global HERO_CACHE
  if HERO_CACHE:
    return HERO_CACHE
  try:
    url = "https://api.opendota.com/api/heroes"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Dota2DraftHelper)"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
      heroes = json.loads(resp.read().decode("utf-8"))
      HERO_CACHE = {h["id"]: h["localized_name"] for h in heroes}
  except Exception as e:
    print(f"Ошибка загрузки списка героев OpenDota: {e}")
  return HERO_CACHE


def clean_hero_name(raw_name: str) -> str:
  if not raw_name:
    return ""
  if "/" in raw_name:
    return raw_name.split("/")[0].strip()
  return raw_name.strip()


def find_hero_id_by_name(name: str, heroes_map: dict) -> int | None:
  cleaned = clean_hero_name(name).lower()
  if not cleaned:
    return None

  for h_id, h_name in heroes_map.items():
    if h_name.lower() == cleaned:
      return h_id

  for h_id, h_name in heroes_map.items():
    if cleaned in h_name.lower() or h_name.lower() in cleaned:
      return h_id
  return None


def get_enemy_counters_stats(enemy_hero_ids: list[int], heroes_map: dict) -> str:
  if not enemy_hero_ids:
    return "Вражеские герои не указаны или не найдены в базе."

  candidate_stats = {}

  for enemy_id in enemy_hero_ids:
    try:
      url = f"https://api.opendota.com/api/heroes/{enemy_id}/matchups"
      req = urllib.request.Request(
          url, headers={"User-Agent": "Mozilla/5.0 (Dota2DraftHelper)"}
      )
      with urllib.request.urlopen(req, timeout=3) as resp:
        matchups = json.loads(resp.read().decode("utf-8"))
        for m in matchups:
          cid = m["hero_id"]
          games = m["games_played"]
          enemy_wins = m["wins"]
          candidate_wins = games - enemy_wins

          if cid not in candidate_stats:
            candidate_stats[cid] = {"wins": 0, "games": 0}
          candidate_stats[cid]["wins"] += candidate_wins
          candidate_stats[cid]["games"] += games
    except Exception as e:
      print(f"Ошибка при получении матчей для врага ID {enemy_id}: {e}")

  if not candidate_stats:
    return (
        "Не удалось загрузить данные из OpenDota (таймаут или ошибка API)."
    )

  results = []
  for cid, data in candidate_stats.items():
    if data["games"] >= 50:
      wr = (data["wins"] / data["games"]) * 100
      results.append((cid, wr, data["games"]))

  results.sort(key=lambda x: x[1], reverse=True)

  top_counters = []
  for cid, wr, games in results[:10]:
    hero_name = heroes_map.get(cid, f"Hero {cid}")
    top_counters.append(
        f"- {hero_name}: {wr:.1f}% винрейт против этого состава врагов ({games}"
        " сыгранных матчей в базе)"
    )

  return "\n".join(top_counters)


@app.get("/")
async def root():
  return RedirectResponse(url="/site")


app.mount(
    "/site", StaticFiles(directory="static", html=True), name="static"
)


@app.post("/api/analyze")
async def analyze_draft(data: DraftRequest):
  try:
    heroes_map = get_opendota_heroes()

    enemy_ids = []
    for e in data.enemy_team:
      hid = find_hero_id_by_name(e, heroes_map)
      if hid:
        enemy_ids.append(hid)

    opendota_stats = get_enemy_counters_stats(enemy_ids, heroes_map)

    my_team_str = f"""
- Поз 1 (Керри): {data.my_team.pos1 or "НЕ ВЫБРАН"}
- Поз 2 (Мид): {data.my_team.pos2 or "НЕ ВЫБРАН"}
- Поз 3 (Тройка/Оффлейн): {data.my_team.pos3 or "НЕ ВЫБРАН"}
- Поз 4 (Четверка/Частичная поддержка): {data.my_team.pos4 or "НЕ ВЫБРАН"}
- Поз 5 (Пятерка/Полная поддержка): {data.my_team.pos5 or "НЕ ВЫБРАН"}
""".strip()

    enemies = [e for e in data.enemy_team if e.strip()]
    enemy_team_str = ", ".join(enemies) if enemies else "Герои не раскрыты"

    prompt = f"""
Ты — профессиональный аналитик драфта Dota 2.

МОЯ КОМАНДА ПО РОЛЯМ:
{my_team_str}

КОМАНДА ПРОТИВНИКА:
{enemy_team_str}

СТАТИСТИКА ИЗ ИСТОРИИ МАТЧЕЙ OPENDOTA (Топ контрпики против выбранных врагов):
{opendota_stats}

СТРОГИЕ ПРАВИЛА:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать эмодзи и спецсимволы разметки: звездочки (**), решетки (#), подчеркивания (_). Пиши только чистым текстом!
2. Для каждой свободной позиции ("НЕ ВЫБРАН") порекомендуй героя, ОБЯЗАТЕЛЬНО УКАЗЫВАЯ ЕГО ВИНРЕЙТ ИЗ ДАННЫХ OPENDOTA в скобках.
3. Никаких приветствий. Начинай сразу с рекомендаций.

ФОРМАТ ОТВЕТА:

Кого взять на свободные роли:
• [Поз X / Герой] (Винрейт по OpenDota: X%) — [1 короткое предложение с причиной]
• [Поз X / Герой] (Винрейт по OpenDota: X%) — [1 короткое предложение с причиной]

Стартовый закуп:
• [Позиция/Линия]: [список предметов]
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash", contents=prompt
    )
    return {"analysis": response.text}
  except Exception as e:
    return {"analysis": f"Ошибка сервиса: {str(e)}"}
