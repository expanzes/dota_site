import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from routers import auth, draft

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    auth.ensure_tables_exist()

# Подключаем папку со статикой
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем API роутеры
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

# Версия для кеш-бастинга
STATIC_VERSION = os.getenv("RENDER_GIT_COMMIT", "dev")[:8]

def serve_page(file_name: str):
    file_path = f"static/{file_name}"
    if not os.path.exists(file_path):
        return HTMLResponse(content="<h1>404: Страница не найдена</h1>", status_code=404)
    
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Вклейка версий CSS/JS
    html = html.replace('/static/css/styles.css"', f'/static/css/styles.css?v={STATIC_VERSION}"')
    for js in ["auth.js", "favorites.js", "draft.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
    return HTMLResponse(content=html)

@app.get("/")
async def get_home():
    return serve_page("index.html")

@app.get("/drafts")
async def get_drafts():
    return serve_page("drafts.html")

@app.get("/fantasy")
async def get_fantasy():
    return serve_page("fantasy.html")

@app.get("/invoker")
async def get_invoker():
    return serve_page("invoker.html")

@app.get("/profile")
async def get_profile():
    return serve_page("profile.html")
