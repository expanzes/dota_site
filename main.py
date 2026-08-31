import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from routers import auth, draft

app = FastAPI()

# УЛУЧШЕННЫЕ НАСТРОЙКИ СЕССИИ
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-key"),
    session_cookie="dota_helper_session",
    same_site="lax",  # Позволяет кукам работать при редиректах со сторонних сайтов (Steam)
    https_only=True   # Обязательно для Render (так как там HTTPS)
)

@app.on_event("startup")
async def startup_event():
    auth.ensure_tables_exist()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

STATIC_VERSION = os.getenv("RENDER_GIT_COMMIT", "dev")[:8]

def serve_page(file_name: str, css_module: str = None):
    file_path = f"static/{file_name}"
    if not os.path.exists(file_path):
        return HTMLResponse(content="<h1>404</h1>", status_code=404)
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    css_links = f'<link rel="stylesheet" href="/static/css/global.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/header.css?v={STATIC_VERSION}">'
    if css_module:
        css_links += f'\n    <link rel="stylesheet" href="/static/css/{css_module}.css?v={STATIC_VERSION}">'
    
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', css_links)
    for js in ["auth.js", "favorites.js", "draft.js", "invoker.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
    return HTMLResponse(content=html)

@app.get("/", response_class=HTMLResponse)
async def get_home(): return serve_page("index.html")

@app.get("/drafts", response_class=HTMLResponse)
async def get_drafts(): return serve_page("drafts.html", "drafts")

@app.get("/profile", response_class=HTMLResponse)
async def get_profile(): return serve_page("profile.html", "profile")

@app.get("/invoker", response_class=HTMLResponse)
async def get_invoker(): return serve_page("invoker.html", "invoker")

@app.get("/fantasy", response_class=HTMLResponse)
async def get_fantasy(): return serve_page("fantasy.html")
