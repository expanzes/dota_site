import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from routers import auth, draft

app = FastAPI()

# Выполняется один раз при запуске сервера
@app.on_event("startup")
async def startup_event():
    auth.ensure_tables_exist()

# Подключаем папку со статикой (изображения, стили, скрипты)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем логику API
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

# Render прокидывает хеш коммита — используем для обновления кеша у пользователей
STATIC_VERSION = os.getenv("RENDER_GIT_COMMIT", "dev")[:8]

def serve_page(file_name: str, css_module: str = None):
    """
    Универсальная функция для отдачи HTML.
    Автоматически заменяет одну строку стилей на набор из:
    global.css + header.css + нужный_модуль.css
    """
    file_path = f"static/{file_name}"
    if not os.path.exists(file_path):
        return HTMLResponse(content="<h1>404: Страница не найдена</h1>", status_code=404)
    
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Формируем список подключений CSS
    css_links = f'<link rel="stylesheet" href="/static/css/global.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/header.css?v={STATIC_VERSION}">'
    
    if css_module:
        css_links += f'\n    <link rel="stylesheet" href="/static/css/{css_module}.css?v={STATIC_VERSION}">'
    
    # Ищем в HTML строку со styles.css и заменяем её на наш пак модулей
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', css_links)
    
    # Прокидываем версию в JS файлы для обновления кеша
    for js in ["auth.js", "favorites.js", "draft.js", "invoker.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
        
    return HTMLResponse(content=html)

# --- ГЛАВНЫЕ РОУТЫ СТРАНИЦ ---

@app.get("/", response_class=HTMLResponse)
async def get_home():
    # Главная страница (меню) не требует спец. модулей, только global и header
    return serve_page("index.html")

@app.get("/drafts", response_class=HTMLResponse)
async def get_drafts():
    # Страница драфтов подгружает drafts.css
    return serve_page("drafts.html", "drafts")

@app.get("/profile", response_class=HTMLResponse)
async def get_profile():
    # Страница профиля подгружает profile.css
    return serve_page("profile.html", "profile")

@app.get("/invoker", response_class=HTMLResponse)
async def get_invoker():
    # Страница тренажера подгружает invoker.css
    return serve_page("invoker.html", "invoker")

@app.get("/fantasy", response_class=HTMLResponse)
async def get_fantasy():
    # Для фэнтези пока нет отдельного CSS, отдаем базу
    return serve_page("fantasy.html")
