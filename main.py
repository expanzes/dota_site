import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class MyTeam(BaseModel):
  pos1: str = ""
  pos2: str = ""
  pos3: str = ""
  pos4: str = ""
  pos5: str = ""


class DraftRequest(BaseModel):
  my_team: MyTeam
  enemy_team: list[str]


@app.get("/")
async def root():
  return RedirectResponse(url="/site")


app.mount(
    "/site", StaticFiles(directory="static", html=True), name="static"
)


@app.post("/api/analyze")
async def analyze_draft(data: DraftRequest):
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

СТРОГИЕ ПРАВИЛА ОФОРМЛЕНИЯ:
1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать эмодзи (смайлики) и символы разметки: звездочки (**), решетки (#), подчеркивания (_). Пиши только чистым текстом!
2. НИКАКИХ приветствий и вступлений. Начинай сразу с рекомендаций.
3. Посмотри, какие роли в "Моей команде" отмечены как "НЕ ВЫБРАН". Порекомендуй лучших героев ИМЕННО на эти свободные роли против драфта врага.

ФОРМАТ ОТВЕТА:

Кого взять на свободные роли:
• [Роль/Герой 1] — [1 короткое предложение почему]
• [Роль/Герой 2] — [1 короткое предложение почему]

Стартовый закуп:
• [Позиция/Линия]: [список начальных предметов]
"""

  def generate():
    response = client.models.generate_content_stream(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=450,  # Запас токенов без обрезки текста
            temperature=0.2,  # Низкое значение ускоряет генерацию
        ),
  )
    for chunk in response:
      if chunk.text:
        yield chunk.text

  return StreamingResponse(generate(), media_type="text/plain")
