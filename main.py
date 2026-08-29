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

@app.get("/")
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace('/static/css/styles.css"', f'/static/css/styles.css?v={STATIC_VERSION}"')
    for js in ["auth.js", "favorites.js", "draft.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
    return HTMLResponse(content=html)
