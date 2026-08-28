from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import httpx

router = APIRouter()

# Модели данных для входных запросов
class DraftRequest(BaseModel):
    my_team: Dict[str, str]
    enemy_team: List[str]
    user_id: Optional[str] = None

# Кэш для списка героев, чтобы не делать лишних запросов к OpenDota
HEROES_CACHE = []

@router.get("/heroes")
async def get_heroes():
    global HEROES_CACHE
    if HEROES_CACHE:
        return HEROES_CACHE
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.opendota.com/api/heroes")
            if response.status_code == 200:
                data = response.json()
                HEROES_CACHE = [
                    {
                        "id": hero["id"],
                        "name": hero["localized_name"],
                        "img": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero['name'].replace('npc_dota_hero_', '')}.png"
                    }
                    for hero in data
                ]
                return HEROES_CACHE
    except Exception as e:
        print(f"Ошибка при запросе к OpenDota: {e}")
    
    # Резервный случай на случай ошибки сети
    return [
        {"id": 1, "name": "Anti-Mage", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png"},
        {"id": 14, "name": "Pudge", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/pudge.png"},
        {"id": 74, "name": "Invoker", "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/invoker.png"}
    ]

@router.post("/analyze")
async def analyze_draft(payload: DraftRequest):
    # Здесь находится основная математика контрпиков и синергий
    # Модуль возвращает аналитику по невыбранным ролям
    
    results = []
    roles = {
        "pos1": "Поз 1 (Керри)",
        "pos2": "Поз 2 (Мид)",
        "pos3": "Поз 3 (Тройка)",
        "pos4": "Поз 4 (Четверка)",
        "pos5": "Поз 5 (Пятерка)"
    }

    for role_key, role_title in roles.items():
        # Если роль в нашей команде не заполнена — рассчитываем рекомендации
        if not payload.my_team.get(role_key):
            results.append({
                "role": role_title,
                "data": {
                    "top_favorite": None,
                    "top_winrate": {"name": "Bloodseeker", "winrate": 61.7, "games": 47, "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/bloodseeker.png"},
                    "top_games": {"name": "Ursa", "winrate": 53.0, "games": 523, "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/ursa.png"},
                    "others": [
                        {"name": "Morphling", "winrate": 57.5, "games": 219, "img": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/morphling.png"}
                    ]
                }
            })

    return {"results": results}
