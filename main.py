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

# Глобальный кэш героев OpenDota, чтобы не запрашивать список каждый раз
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
  """Загружает список героев из OpenDota API."""
  global HERO_CACHE
  if HERO_CACHE:
    return HERO_CACHE
  try:
    url = "https://api.opendota.com/api/heroes"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Dota2DraftHelper)"}
    )
    with urllib.request.urlopen(req, timeout=4) as resp:
      heroes = json.loads(resp.read().decode("utf-8"))
      HERO_CACHE = {h["id"]: h["localized_name"] for h in heroes}
  except Exception as e:
    print(f"Ошибка при загрузке списка героев OpenDota: {e}")
  return HERO_CACHE


def clean_hero_name(raw_name: str) -> str:
  """Очищает строку вида 'Jakiro / Джакиро' до 'Jakiro'."""
  if not raw_name:
    return ""
  if "/" in raw_name:
    return raw_name.split("/")[0].strip()
  return raw_name.strip()


def find_hero_id_by_name(name: str, heroes_map: dict) -> int | None:
  """Находит OpenDota hero_id по названию."""
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
  """Рассчитывает статистику контрпиков из базы данных OpenDota."""
  if not enemy_hero_ids:
    return ""

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
          candidate_wins = games - enemy_wins  # Победы контрпика

          if cid not in candidate_stats:
            candidate_stats[cid] = {"wins": 0, "games": 0}
          candidate_stats[cid]["wins"] += candidate_wins
          candidate_stats[cid]["games"] += games
    except Exception as e:
      print(f"Ошибка при запросе матчей для врага {enemy_id}: {e}")

  # Считаем винрейт каждого героя против выбранного пика врагов
  results = []
  for cid, data in candidate_stats.items():
    if data["games"] >= 100:  # берем репрезентативную выборку
      wr = (data["wins"] / data["games"]) * 100
      results.append((cid, wr, data["games"]))

  results.sort(key=lambda x: x[1], reverse=True)

  top_counters = []
  for cid, wr, games in results[:10]:
    hero_name = heroes_map.get(cid, f"Hero {cid}")
    top_counters.append(
        f"- {hero_name}: {wr:.1f}% винрейт против выбранных врагов ({games}"
        " сыгранных матчей)"
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

    # Поиск ID выбранных врагов
    enemy_ids = []
    for e in data.enemy_team:
      hid = find_hero_id_by_name(e, heroes_map)
      if hid:
        enemy_ids.append(hid)

    # Запрос реальной статистики из OpenDota
    opendota_stats = get_enemy_counters_stats(enemy_ids, heroes_map)
    if not opendota_stats:
      opendota_stats = "Данные о винрейтах из OpenDota недоступны или вражеские герои не выбраны."

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
Ты — профессиональный аналитик драфта Dota 2. Дай МАКСИМАЛЬНО КРАТКИЙ И ЧЕТКИЙ ответ во время пиков.

МОЯ КОМАНДА ПО РОЛЯМ:
{my_team_str}

КОМАНДА ПРОТИВНИКА:
{enemy_team_str}

РЕАЛЬНАЯ СТАТИСТИКА ИЗ ИСТОРИИ МАТЧЕЙ OPENDOTA (Топ контрпики против драфта врага):
{opendota_stats}

СТРОГИЕ ПРАВИЛА ОФОРМЛЕНИЯ:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать эмодзи (смайлики) и символы разметки: звездочки (**), решетки (#), подчеркивания (_). Пиши только чистым текстом!
2. Опирайся на приведенную статистику OpenDota, подбирая героев с высоким винрейтом под свободные роли ("НЕ ВЫБРАН").
3. НИКАКИХ приветствий и вступлений. Начинай сразу с рекомендаций.

ФОРМАТ ОТВЕТА:

Кого взять на свободные роли:
• [Роль/Герой 1] — [1 короткое предложение с упором на статистику/причину]
• [Роль/Герой 2] — [1 короткое предложение с упором на статистику/причину]

Стартовый закуп:
• [Позиция/Линия]: [список начальных предметов]
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    return {"analysis": response.text}
  except Exception as e:
    return {"analysis": f"Ошибка сервиса: {str(e)}"}
