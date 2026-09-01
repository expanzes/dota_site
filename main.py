import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from routers import auth, draft

app = FastAPI()

# Middleware для сессий (необходимо для работы авторизации и Steam)
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "dota-helper-secret-999"),
    session_cookie="dota_helper_session",
    same_site="lax",
    https_only=True  # Обязательно для работы через Cloudflare/Amvera (HTTPS)
)

@app.on_event("startup")
async def startup_event():
    # Проверка и создание таблиц в базе данных Neon при запуске
    auth.ensure_tables_exist()

# Монтируем папку со статикой (стили, скрипты, картинки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем логику API из папки routers
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

# Версия статики для сброса кэша в браузере
STATIC_VERSION = "2.0.5"

def serve_page(file_name: str, module_name: str = None):
    """
    Функция для отдачи HTML-файлов.
    Она автоматически собирает пак стилей и прокидывает версии в JS.
    """
    file_path = f"static/{file_name}"
    
    # Проверка на существование файла
    if not os.path.exists(file_path):
        return HTMLResponse(content="<h1>404: Страница не найдена</h1>", status_code=404)
        
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Собираем пак стилей в строгом порядке: 
    # Global (база) -> Components (кнопки/тултипы) -> Header (шапка)
    css_links = f'<link rel="stylesheet" href="/static/css/global.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/components.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/header.css?v={STATIC_VERSION}">'
    
    # Если у страницы есть свой уникальный CSS (например, drafts.css)
    if module_name:
        css_links += f'\n    <link rel="stylesheet" href="/static/css/{module_name}.css?v={STATIC_VERSION}">'
    
    # Заменяем временную метку в HTML на наш пак стилей
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', css_links)
    
    # Добавляем версию ко всем JS файлам, чтобы браузер не брал старые из памяти
    for js in ["auth.js", "favorites.js", "draft.js", "invoker.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
        
    return HTMLResponse(content=html)

# --- МАРШРУТЫ ДЛЯ СТРАНИЦ САЙТА ---

@app.get("/")
async def get_home(): 
    return serve_page("index.html")

@app.get("/drafts")
async def get_drafts(): 
    return serve_page("drafts.html", "drafts")

@app.get("/profile")
async def get_profile(): 
    return serve_page("profile.html", "profile")

@app.get("/invoker")
async def get_invoker(): 
    return serve_page("invoker.html", "invoker")

@app.get("/fantasy")
async def get_fantasy(): 
    return serve_page("fantasy.html")
