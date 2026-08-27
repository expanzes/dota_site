from concurrent.futures import ThreadPoolExecutor
import json
import os
import ssl
import time
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

ROLES_DB = {
    "pos1": {
        "phantom lancer", "anti-mage", "juggernaut", "sven", "spectre", "faceless void",
        "morphling", "ursa", "terrorblade", "slark", "luna", "medusa", "gyrocopter",
        "chaos knight", "lifestealer", "drow ranger", "troll warlord", "monkey king",
        "weaver", "muerta", "phantom assassin", "bloodseeker", "clinkz", "arc warden"
    },
    "pos2": {
        "storm spirit", "ember spirit", "void spirit", "earth spirit", "puck", "lina",
        "leshrac", "invoker", "tinker", "queen of pain", "shadow fiend", "templar assassin",
        "dragon knight", "sniper", "zeus", "death prophet", "pangolier", "batrider",
        "meepo", "kunkka", "huskar", "viper", "necrophos", "outworld devourer", "tiny",
        "primal beast", "windranger", "pudge", "razor", "nature's prophet", "arc warden",
        "alchemist", "broodmother", "visage", "silencer"
    },
    "pos3": {
        "axe", "centaur warrunner", "mars", "tidehunter", "bristleback", "slardar",
        "underlord", "doom", "timbersaw", "magnus", "night stalker", "dawnbreaker",
        "beastmaster", "enigma", "dark seer", "legion commander", "viper", "primal beast",
        "abaddon", "brewmaster", "sand king", "lycan"
    },
    "pos4": {
        "tusk", "hoodwink", "clockwerk", "mirana", "bounty hunter", "nyx assassin",
        "earthshaker", "rubick", "tiny", "pugna", "techies", "dark willow", "snapfire",
        "skywrath mage", "marci"
    },
    "pos5": {
        "jakiro", "bane", "ancient apparition", "lion", "shadow shaman", "crystal maiden",
        "witch doctor", "ogre magi", "disruptor", "oracle", "grimstroke", "dazzle",
        "treant protector", "chen", "enchantress", "keeper of the light", "undying", "lich"
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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as resp:
      heroes = json.loads(resp.read().decode("utf-8"))
      HERO_CACHE = {h["id"]: h["localized_name"] for h in heroes}
  except Exception as e:
    print(f"Error fetching heroes: {e}")
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


def fetch_matchup_for_hero(enemy_id: int):
  global MATCHUPS_CACHE
  if enemy_id in MATCHUPS_CACHE:
    return MATCHUPS_CACHE[enemy_id]

  url = f"https://api.opendota.com/api/heroes/{enemy_id}/matchups"
  headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

  try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as resp:
      data = json.loads(resp.read().decode("utf-8"))
      if isinstance(data, list) and len(data) > 0:
        MATCHUPS_CACHE[enemy_id] = data
        return data
  except Exception as e:
    print(f"Error fetching matchup for {enemy_id}: {e}")

  return None


def get_recommendations_for_role(role_key: str, candidate_stats: dict, heroes_map: dict) -> list[str]:
  valid_heroes_for_role = ROLES_DB.get(role_key, set())
  
  all_candidates = []
  role_candidates = []

  for cid, data in candidate_stats.items():
    hero_name = heroes_map.get(cid, "")
    if not hero_name or data["games"] == 0:
      continue

    wr = (data["wins"] / data["games"]) * 100
    item = (hero_name, wr, data["games"])

    all_candidates.append(item)
    if hero_name.lower() in valid_heroes_for_role:
      role_candidates.append(item)

  role_candidates.sort(key=lambda x: x[1], reverse=True)
  all_candidates.sort(key=lambda x: x[1], reverse=True)

  final_list = role_candidates if role_candidates else all_candidates

  formatted = []
  if final_list:
    best_hero, best_wr, best_games = final_list[0]
    formatted.append(f"  ★ САМЫЙ ЛУЧШИЙ ПИК: {best_hero} — {best_wr:.1f}% винрейт (матчей: {best_games})")
    
    if len(final_list) > 1:
      formatted.append("  Другие сильные варианты:")
      for h_name, wr, games in final_list[1:4]:
        formatted.append(f"    • {h_name}: {wr:.1f}% винрейт (матчей: {games})")
  else:
    formatted.append("  • Не удалось подобрать героя")

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
  
  # Последовательный опрос с паузой предотвращает 429
  for enemy_id in enemy_ids:
    matchups = fetch_matchup_for_hero(enemy_id)
    if not matchups:
      time.sleep(0.2)
      matchups = fetch_matchup_for_hero(enemy_id)

    if matchups:
      for m in matchups:
        cid = m["hero_id"]
        games = m["games_played"]
        enemy_wins = m["wins"]
        candidate_wins = games - enemy_wins

        if cid not in candidate_stats:
          candidate_stats[cid] = {"wins": 0, "games": 0}
        candidate_stats[cid]["wins"] += candidate_wins
        candidate_stats[cid]["games"] += games
    
    time.sleep(0.05)

  empty_positions = {
      "pos1": ("Поз 1 (Керри)", data.my_team.pos1),
      "pos2": ("Поз 2 (Мид)", data.my_team.pos2),
      "pos3": ("Поз 3 (Тройка)", data.my_team.pos3),
      "pos4": ("Поз 4 (Четверка)", data.my_team.pos4),
      "pos5": ("Поз 5 (Пятерка)", data.my_team.pos5),
  }

  output_lines = ["Результат анализа драфта по базе OpenDota:\n"]
  found_any = False

  for role_key, (role_title, selected_hero) in empty_positions.items():
    if not selected_hero or selected_hero.strip() == "":
      found_any = True
      recs = get_recommendations_for_role(role_key, candidate_stats, heroes_map)
      output_lines.append(f"{role_title}:")
      output_lines.extend(recs)
      output_lines.append("")

  if not found_any:
    output_lines.append("Все роли в вашей команде уже заполнены!")

  return {"analysis": "\n".join(output_lines)}
