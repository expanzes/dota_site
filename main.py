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
- Поз 1: {data.my_team.pos1 or "НЕ ВЫБРАН"}
- Поз 2: {data.my_team.pos2 or "НЕ ВЫБРАН"}
- Поз 3: {data.my_team.pos3 or "НЕ ВЫБРАН"}
- Поз 4: {data.my_team.pos4 or "НЕ ВЫБРАН"}
- Поз 5: {data.my_team.pos5 or "НЕ ВЫБРАН"}
""".strip()

  enemies = [e for e in data.enemy_team if e.strip()]
  enemy_team_str = ", ".join(enemies) if enemies else "Герои не раскрыты"

  prompt = f"""
Ты — помощник по драфту Dota 2. Дай быстрый и четкий ответ.

МОЯ КОМАНДА:
{my_team_str}

ВРАГИ:
{enemy_team_str}

ПРАВИЛА:
1. КАТЕГОРИЧЕСКИ НЕ ИСПОЛЬЗУЙ эмодзи и спецсимволы разметки: звездочки (*), решетки (#), двоеточия перед тире. Пиши простым текстом.
2. Пиши кратко: по 1 предложению на героя.
3. Порекомендуй героев только на свободные позиции ("НЕ ВЫБРАН").

СТРУКТУРА ОТВЕТА:

Рекомендуемые пики:
- [Позиция] [Герой] - [причина в 1 предложение]

Стартовый закуп:
- [Позиция]: [список предметов]
"""

  def generate():
    response = client.models.generate_content_stream(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=1000,  # Запас токенов, чтобы ответ не обрывался
            temperature=0.2,
        ),
    )
    for chunk in response:
      if chunk.text:
        yield chunk.text

  return StreamingResponse(generate(), media_type="text/plain")
