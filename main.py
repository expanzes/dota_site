import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/")
async def root():
    return RedirectResponse(url="/site")

app.mount("/site", StaticFiles(directory="static", html=True), name="static")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class DraftData(BaseModel):
    radiant: list[str]
    dire: list[str]

@app.post("/api/analyze")
async def analyze_draft(data: DraftData):
    try:
        prompt = f"""
Ты — быстрый ассистент по драфту Dota 2. Твоя задача — дать МАКСИМАЛЬНО КОРОТКИЙ и четкий ответ во время пиков. У игрока мало времени!

Состав Radiant: {', '.join(data.radiant)}
Состав Dire: {', '.join(data.dire)}

СТРОГИЕ ПРАВИЛА:
1. НИКАКИХ приветствий, вступлений, вежливости и водных фраз ("Приветствую", "Давайте разберем", "На связи аналитик" СТРОГО ЗАПРЕЩЕНЫ). Начинай сразу с дела!
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
        return {"error": str(e)}