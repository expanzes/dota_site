from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth, draft

app = FastAPI()

# Подключаем папку со статикой (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем логику авторизации и драфта
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

# Главная страница сайта
@app.get("/")
async def read_index():
    return FileResponse("static/index.html")
