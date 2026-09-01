def serve_page(file_name: str, module_name: str = None):
    file_path = f"static/{file_name}"
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Пак стилей теперь включает components.css
    css_links = f'<link rel="stylesheet" href="/static/css/global.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/components.css?v={STATIC_VERSION}">'
    css_links += f'\n    <link rel="stylesheet" href="/static/css/header.css?v={STATIC_VERSION}">'
    if module_name:
        css_links += f'\n    <link rel="stylesheet" href="/static/css/{module_name}.css?v={STATIC_VERSION}">'
    
    html = html.replace('<link rel="stylesheet" href="/static/css/styles.css">', css_links)
    
    for js in ["auth.js", "favorites.js", "draft.js", "invoker.js"]:
        html = html.replace(f'/static/js/{js}"', f'/static/js/{js}?v={STATIC_VERSION}"')
        
    return HTMLResponse(content=html)
