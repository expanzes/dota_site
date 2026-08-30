import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from routers import auth, draft

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    auth.ensure_tables_exist()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

STATIC_VERSION = os.getenv("RENDER_GIT_COMMIT", "dev")[:8]

def serve_page(file_name: str, css_module: str = None):
    file_path = f"static/{file_name}"
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Всегда подключаем global и header
    css_links = f'<link rel="stylesheet" href="/static/css/global.css?v={STATIC_VERSION}">'
    css_links += f'\n<link rel="stylesheet" href="/static/css/header.css?v={STATIC_VERSION}">'
    
    # Подключаем специфический модуль (например, drafts.css)
    if css_module:
        css_links += f'\n<link rel="stylesheet" href="/static/css/{css_module}.css?v={STATIC_VERSION}">'
    
    # Заменяем старую ссылку на новые
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', css_links)
    
    # Прокидываем версии в JS
    for js in ["auth.js", "favorites.js", "draft.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
    
    return HTMLResponse(content=html)

@app.get("/")
async def get_home(): return serve_page("index.html")

@app.get("/drafts")
async def get_drafts(): return serve_page("drafts.html", "drafts")

@app.get("/profile")
async def get_profile(): return serve_page("profile.html", "profile")

# Для остальных страниц
@app.get("/fantasy")
async def get_fantasy(): return serve_page("fantasy.html")
@app.get("/invoker")
async def get_invoker(): return serve_page("invoker.html")
