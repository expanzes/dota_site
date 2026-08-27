import json
import ssl
import time
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
      HERO_CACHE = {
          h["id"]: {
              "name": h["localized_name"],
              "slug": h["name"].replace("npc_dota_hero_", ""),
          }
          for h in heroes
      }
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
  for h_id, data in heroes_map.items():
    if data["name"].lower() == cleaned:
      return h_id
  for h_id, data in heroes_map.items():
    if cleaned in data["name"].lower() or data["name"].lower() in cleaned:
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


def get_role_data(role_key: str, candidate_stats: dict, heroes_map: dict):
  valid_heroes = ROLES_DB.get(role_key, set())
  role_candidates = []
  all_candidates = []

  for cid, data in candidate_stats.items():
    hero_info = heroes_map.get(cid)
    if not hero_info or data["games"] < 30:
      continue

    wr = (data["wins"] / data["games"]) * 100
    img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_info['slug']}.png"
    item = {
        "name": hero_info["name"],
        "winrate": round(wr, 1),
        "games": data["games"],
        "img": img_url,
    }

    all_candidates.append(item)
    if hero_info["name"].lower() in valid_heroes:
      role_candidates.append(item)

  # Фолбэк на выборку от 10 игр
  if not role_candidates and not all_candidates:
    for cid, data in candidate_stats.items():
      hero_info = heroes_map.get(cid)
      if hero_info and data["games"] >= 10:
        wr = (data["wins"] / data["games"]) * 100
        img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero_info['slug']}.png"
        item = {
            "name": hero_info["name"],
            "winrate": round(wr, 1),
            "games": data["games"],
            "img": img_url,
        }
        all_candidates.append(item)
        if hero_info["name"].lower() in valid_heroes:
          role_candidates.append(item)

  role_candidates.sort(key=lambda x: x["winrate"], reverse=True)
  all_candidates.sort(key=lambda x: x["winrate"], reverse=True)

  final_list = role_candidates if role_candidates else all_candidates
  if not final_list:
    return None

  return {
      "best": final_list[0],
      "alternatives": final_list[1:4] if len(final_list) > 1 else [],
  }


@app.get("/")
async def root():
  return RedirectResponse(url="/site")


app.mount("/site", StaticFiles(directory="static", html=True), name="static")


@app.post("/api/analyze")
async def analyze_draft(data: DraftRequest):
  heroes_map = get_opendota_heroes()

  enemy_ids = []
  for e in data.enemy_team:
    hid = find_hero_id_by_name(e, heroes_map)
    if hid:
      enemy_ids.append(hid)

  if not enemy_ids:
    return {
        "status": "error",
        "message": "Выберите хотя бы одного вражеского героя.",
    }

  candidate_stats = {}
  for enemy_id in enemy_ids:
    matchups = fetch_matchup_for_hero(enemy_id)
    if matchups:
      for m in matchups:
        cid = m["hero_id"]
        games = m["games_played"]
        candidate_wins = games - m["wins"]

        if cid not in candidate_stats:
          candidate_stats[cid] = {"wins": 0, "games": 0}
        candidate_stats[cid]["wins"] += candidate_wins
        candidate_stats[cid]["games"] += games
    time.sleep(0.05)

  empty_positions = {
      "pos1": "Поз 1 (Керри)",
      "pos2": "Поз 2 (Мид)",
      "pos3": "Поз 3 (Тройка)",
      "pos4": "Поз 4 (Четверка)",
      "pos5": "Поз 5 (Пятерка)",
  }

  results = []
  for role_key, role_title in empty_positions.items():
    user_pick = getattr(data.my_team, role_key)
    if not user_pick or user_pick.strip() == "":
      role_data = get_role_data(role_key, candidate_stats, heroes_map)
      results.append(
          {"role": role_title, "data": role_data}
      )

  return {"status": "ok", "results": results}
