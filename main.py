import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from routers import auth, draft

app = FastAPI()

# Подключаем папку со статикой (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем логику авторизации и драфта
app.include_router(auth.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

# Render автоматически прокидывает хеш последнего коммита в эту переменную —
# используем его как версию для cache-busting статики (CSS/JS).
STATIC_VERSION = os.getenv("RENDER_GIT_COMMIT", "dev")[:8]


# Главная страница сайта
@app.get("/")
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Добавляем ?v=<версия> к ссылкам на CSS/JS, чтобы браузер всегда
    # подгружал актуальную версию файла после деплоя, а не старую из кеша.
    html = html.replace(
        '/static/css/styles.css"',
        f'/static/css/styles.css?v={STATIC_VERSION}"',
    )
    for js_file in ["auth.js", "favorites.js", "draft.js"]:
        html = html.replace(
            f'/static/js/{js_file}"',
            f'/static/js/{js_file}?v={STATIC_VERSION}"',
        )

    return HTMLResponse(content=html)
