import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai

app = FastAPI()

app.mount("/site", StaticFiles(directory="static", html=True), name="static")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class DraftData(BaseModel):
    radiant: list[str]
    dire: list[str]

@app.post("/api/analyze")
async def analyze_draft(data: DraftData):
    try:
        prompt = f"""
        Ты — профессиональный киберспортивный аналитик Dota 2.
        
        Состав Radiant (Силы Света): {', '.join(data.radiant)}
        Состав Dire (Силы Тьмы): {', '.join(data.dire)}
        
        1. Проанализируй пики и выдели TOP-3 лучших контрпика для нашей команды.
        2. Дай краткий план на игру и рекомендуемый стартовый закуп.
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return {"analysis": response.text}
    except Exception as e:
        return {"analysis": f"❌ Ошибка обращения к Gemini: {str(e)}"}