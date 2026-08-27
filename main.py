import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from google import genai
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
Ты — помощник по драфту Dota 2. Пиши сразу к делу, без приветствий и длинных вводных фраз.

Состав Radiant: {radiant_team}
Состав Dire: {dire_team}

Предложи лучших героев для допика (с кратким пояснением) и начальный закуп.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    return {"analysis": response.text}
  except Exception as e:
    return {"analysis": f"Ошибка сервиса: {str(e)}"}
