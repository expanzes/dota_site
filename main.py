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

HERO_CACHE = {}
MATCHUPS_CACHE = {}

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Списки героев по ролям для фильтрации
ROLES_DB = {
    "pos1": {
        "Phantom Lancer", "Anti-Mage", "Juggernaut", "Sven", "Spectre", "Faceless Void",
        "Morphling", "Ursa", "Terrorblade", "Slark", "Luna", "Medusa", "Gyrocopter",
        "Chaos Knight", "Lifestealer", "Drow Ranger", "Troll Warlord", "Monkey King", "Weaver", "Muerta"
    },
    "pos2": {
        "Storm Spirit", "Ember Spirit", "Void Spirit", "Earth Spirit", "Puck", "Lina",
        "Leshrak", "Invoker", "Tinker", "Queen of Pain", "Shadow Fiend", "Templar Assassin",
        "Dragon Knight", "Sniper", "Zeus", "Death Prophet", "Pangolier", "Batrider",
        "Meepo", "Kunkka", "Huskar", "Viper", "Necrophos", "Outworld Destroyer", "Tiny",
        "Primal Beast", "Windranger", "Pudge", "Razor", "Void Spirit", "Nature's Prophet"
    },
    "pos3": {
        "Axe", "Centaur Warrunner", "Mars", "Tidehunter", "Bristleback", "Slardar",
        "Underlord", "Doom", "Timbersaw", "Magnus", "Night Stalker", "Dawnbreaker",
        "Beastmaster", "Enigma", "Dark Seer", "Legion Commander", "Viper", "Primal Beast", "Abaddon"
    },
    "pos4": {
        "Tusk", "Hoodwink", "Clockwerk", "Mirana", "Bounty Hunter", "Nyx Assassin",
        "Earthshaker", "Rubick", "Tiny", "Pugna", "Techies", "Dark Willow", "Snapfire"
    },
    "pos5": {
        "Jakiro", "Bane", "Ancient Apparition", "Lion", "Shadow Shaman", "Crystal Maiden",
        "Witch Doctor", "Ogre Magi", "Disruptor", "Oracle", "Grimstroke", "Dazzle",
        "Treant Protector", "Chen", "Enchantress", "Keeper of the Light", "Undying"
    }
}


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


def get_recommendations_for_role(role_key: str, candidate_stats: dict, heroes_map: dict) -> list[str]:
  """Фильтрует контрпики по роли и винрейту >= 50%."""
  valid_heroes_for_role = ROLES_DB.get(role_key, set())
  results = []

  for cid, data in candidate_stats.items():
    hero_name = heroes_map.get(cid, "")
    if data["games"] < 30:
      continue

    wr = (data["wins"] / data["games"]) * 100
    
    # ФИЛЬТР 1: Только винрейт 50% и выше
    if wr < 50.0:
      continue

    # ФИЛЬТР 2: Проверка соответствия роли (если база ролей не пустая)
    if valid_heroes_for_role and hero_name not in valid_heroes_for_role:
      continue

    results.append((hero_name, wr, data["games"]))

  results.sort(key=lambda x: x[1], reverse=True)
  
  formatted = []
  for h_name, wr, games in results[:5]:
    formatted.append(f"  • {h_name}: {wr:.1f}% винрейт (матчей: {games})")
  
  return formatted


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

  if not enemy_ids:
    return {"analysis": "Выберите хотя бы одного вражеского героя для анализа."}

  candidate_stats = {}
  with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_single_matchup, enemy_ids))

  for enemy_id, matchups, error in results:
    if error or not matchups:
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

  # Проверяем незанятые позиции
  empty_positions = {
      "pos1": ("Поз 1 (Керри)", data.my_team.pos1),
      "pos2": ("Поз 2 (Мид)", data.my_team.pos2),
      "pos3": ("Поз 3 (Тройка)", data.my_team.pos3),
      "pos4": ("Поз 4 (Четверка)", data.my_team.pos4),
      "pos5": ("Поз 5 (Пятерка)", data.my_team.pos5),
  }

  output_lines = ["Рекомендуемые пики на свободные роли (винрейт > 50%):\n"]
  found_any = False

  for role_key, (role_title, selected_hero) in empty_positions.items():
    if not selected_hero or selected_hero.strip() == "":
      found_any = True
      recs = get_recommendations_for_role(role_key, candidate_stats, heroes_map)
      output_lines.append(f"{role_title}:")
      if recs:
        output_lines.extend(recs)
      else:
        output_lines.append("  • Нет подпадающих героев с винрейтом > 50%")
      output_lines.append("")

  if not found_any:
    output_lines.append("Все роли в вашей команде уже заполнены!")

  return {"analysis": "\n".join(output_lines)}
