import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class DraftData(BaseModel):
  radiant: list[str]
  dire: list[str]


@app.get("/")
async def root():
  return RedirectResponse(url="/site")


app.mount(
    "/site", StaticFiles(directory="static", html=True), name="static"
)


@app.post("/api/analyze")
async def analyze_draft(data: DraftData):
  try:
    radiant_team = ", ".join(data.radiant)
    dire_team = ", ".join(data.dire)

    prompt = f"""
Ты — быстрый ассистент по драфту Dota 2. Дай МАКСИМАЛЬНО КОРОТКИЙ и четкий ответ во время пиков.

Состав Radiant: {radiant_team}
Состав Dire: {dire_team}

СТРОГИЕ ПРАВИЛА:
1. НИКАКИХ приветствий и вступлений ("Приветствую", "Давайте разберем" СТРОГО ЗАПРЕЩЕНЫ). Начинай сразу с дела!
2. Не используй символы ** (пиши простым текстом).
3. Пиши кратко: 3 героя и стартовый закуп.

ФОРМАТ ОТВЕТА:

🎯 КИПИ/КОНТРПИКИ:
• [Герой 1] — [1 короткое предложение почему]
• [Герой 2] — [1 короткое предложение почему]
• [Герой 3] — [1 короткое предложение почему]

🎒 СТАРТОВЫЙ ЗАКУП:
• [Роль/Линия 1]: [предметы]
• [Роль/Линия 2]: [предметы]
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=600,  # Запас токенов для полного ответа на русском
            temperature=0.2,
        ),
    )
    return {"analysis": response.text}
  except Exception as e:
    return {"analysis": f"Ошибка сервиса: {str(e)}"}
