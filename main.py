import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from routers import auth, draft

app = FastAPI()

app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "dota-helper-secret-999"),
    session_cookie="dota_helper_session",
    same_site="lax",
    https_only=True
)

@app.on_event("startup")
async def startup_event():
    auth.ensure_tables_exist()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

STATIC_VERSION = "1.0.6"

def serve_page(file_name: str, module_name: str = None):
    file_path = f"static/{file_name}"
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    css_links = f'<link rel="stylesheet" href="/static/css/global.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/header.css?v={STATIC_VERSION}">'
    if module_name:
        css_links += f'\n    <link rel="stylesheet" href="/static/css/{module_name}.css?v={STATIC_VERSION}">'
    
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', css_links)
    
    for js in ["auth.js", "favorites.js", "draft.js", "invoker.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
    return HTMLResponse(content=html)

@app.get("/")
async def get_home(): return serve_page("index.html")

@app.get("/drafts")
async def get_drafts(): return serve_page("drafts.html", "drafts")

@app.get("/profile")
async def get_profile(): return serve_page("profile.html", "profile")

@app.get("/invoker")
async def get_invoker(): return serve_page("invoker.html", "invoker")

@app.get("/fantasy")
async def get_fantasy(): return serve_page("fantasy.html")
