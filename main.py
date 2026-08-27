from concurrent.futures import ThreadPoolExecutor
import json
import os
import ssl
import urllib.error
import urllib.request
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Кэш в памяти для героев и истории матчей
HERO_CACHE = {}
MATCHUPS_CACHE = {}

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


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
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        },
    )
    with urllib.request.urlopen(
        req, timeout=5, context=SSL_CONTEXT
    ) as resp:
      heroes = json.loads(resp.read().decode("utf-8"))
      HERO_CACHE = {h["id"]: h["localized_name"] for h in heroes}
  except Exception as e:
    print(f"Ошибка загрузки героев: {e}")
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


def fetch_single_matchup(enemy_id: int):
  """Параллельное получение матчей для одного вражеского героя."""
  global MATCHUPS_CACHE
  if enemy_id in MATCHUPS_CACHE:
    return enemy_id, MATCHUPS_CACHE[enemy_id], None

  try:
    url = f"https://api.opendota.com/api/heroes/{enemy_id}/matchups"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ),
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(
        req, timeout=6, context=SSL_CONTEXT
    ) as resp:
      data = json.loads(resp.read().decode("utf-8"))
      MATCHUPS_CACHE[enemy_id] = data
      return enemy_id, data, None
  except Exception as e:
    return enemy_id, None, str(e)


def get_enemy_counters_stats(enemy_hero_ids: list[int], heroes_map: dict) -> str:
  if not enemy_hero_ids:
    return "Вражеские герои не выбраны или не найдены в базе."

  candidate_stats = {}
  errors = []

  # Запрашиваем матчи для всех врагов параллельно
  with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_single_matchup, enemy_hero_ids))

  for enemy_id, matchups, error in results:
    if error or not matchups:
      hero_name = heroes_map.get(enemy_id, f"ID {enemy_id}")
      errors.append(f"{hero_name}")
      continue

    for m in matchups:
      cid = m["hero_id"]
      games = m["games_played"]
      enemy_wins = m["wins"]
      candidate_wins = games - enemy_wins

      if cid not in candidate_stats:
        candidate_stats[cid] = {"wins": 0, "games": 0}
      candidate_stats[cid]["wins"] += candidate_wins
      candidate_stats[cid]["games"] += games

  if not candidate_stats:
    err_details = ", ".join(errors) if errors else "Ошибка сети"
    return (
        f"Не удалось загрузить данные из OpenDota по героям: {err_details}."
    )

  results_list = []
  for cid, data in candidate_stats.items():
    if data["games"] >= 50:
      wr = (data["wins"] / data["games"]) * 100
      results_list.append((cid, wr, data["games"]))

  results_list.sort(key=lambda x: x[1], reverse=True)

  top_counters = []
  for cid, wr, games in results_list[:10]:
    hero_name = heroes_map.get(cid, f"Hero {cid}")
    top_counters.append(
        f"• {hero_name}: {wr:.1f}% винрейт (сыграно матчей в базе: {games})"
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
  heroes_map = get_opendota_heroes()

  enemy_ids = []
  for e in data.enemy_team:
    hid = find_hero_id_by_name(e, heroes_map)
    if hid:
      enemy_ids.append(hid)

  opendota_stats = get_enemy_counters_stats(enemy_ids, heroes_map)

  enemies = [e for e in data.enemy_team if e.strip()]
  enemy_team_str = ", ".join(enemies) if enemies else "Герои не выбраны"

  analysis_text = f"""Статистика OpenDota по лучшим контрпикам:

Топ-10 героев по винрейту против состава ({enemy_team_str}):
{opendota_stats}"""

  return {"analysis": analysis_text}
