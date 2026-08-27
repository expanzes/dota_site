import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from pydantic import BaseModel

app = FastAPI()

# Инициализация клиента Gemini
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
Ты — быстрый ассистент по драфту Dota 2. Твоя задача — дать МАКСИМАЛЬНО КОРОТКИЙ и четкий ответ во время пиков.

Состав Radiant: {radiant_team}
Состав Dire: {dire_team}

СТРОГИЕ ПРАВИЛА:
1. НИКАКИХ приветствий и вступлений ("Приветствую", "Давайте разберем" СТРОГО ЗАПРЕЩЕНЫ). Начинай сразу с контрпиков!
2. Пиши кратко, емко и по фактам.

ФОРМАТ ОТВЕТА:

🎯 **Кого взять (Лучшие герои):**
• [Герой 1] — [коротко почему, 1 предложение]
• [Герой 2] — [коротко почему, 1 предложение]
• [Герой 3] — [коротко почему, 1 предложение]

🎒 **Стартовый закуп:**
• [Роль/Линия 1]: [список начальных предметов]
• [Роль/Линия 2]: [список начальных предметов]
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return {"analysis": response.text}
  except Exception as e:
    return {"analysis": f"Ошибка сервиса: {str(e)}"}
