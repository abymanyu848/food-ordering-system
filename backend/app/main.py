from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pathlib import Path
from app.api.v1.api import api_router
from app.settings import settings
from app.database import Base, engine
# Import every model before create_all so all tables and relationships are registered.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create SQLite tables automatically; migrations are unnecessary for this project."""
    import os

    # Skip during testing to allow tests to use their own database
    if os.getenv("TESTING") != "1":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Food Ordering Management System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
uploads_dir = Path(__file__).resolve().parents[1] / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


@app.get("/css/style.css")
async def serve_style_css():
    return FileResponse(frontend_dir / "css" / "style.css", media_type="text/css", headers=NO_CACHE_HEADERS)


app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="frontend-css")


@app.get("/js/{script_path:path}")
async def serve_js(script_path: str):
    file_path = frontend_dir / "js" / script_path
    if file_path.is_file():
        return FileResponse(file_path, media_type="application/javascript")
    return Response(
        content="/* Migrated to CraveCart */ if ('serviceWorker' in navigator) { navigator.serviceWorker.getRegistrations().then(function(r){ for(var i=0;i<r.length;i++) r[i].unregister(); }); } if (!window.__crave_redirected) { window.__crave_redirected = true; window.location.href = '/'; }",
        media_type="application/javascript",
        headers=NO_CACHE_HEADERS,
    )


@app.get("/")
async def root():
    return FileResponse(frontend_dir / "index.html", headers=NO_CACHE_HEADERS)


@app.get("/index.html")
async def index_page():
    return FileResponse(frontend_dir / "index.html", headers=NO_CACHE_HEADERS)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(frontend_dir / "favicon.svg", media_type="image/svg+xml")


@app.get("/style.css")
async def legacy_style_css():
    return FileResponse(frontend_dir / "css" / "style.css", media_type="text/css", headers=NO_CACHE_HEADERS)


@app.get("/{script_name}.js")
async def legacy_js_scripts(script_name: str):
    """Handle legacy scripts gracefully by serving a redirect snippet if a cached tab asks for them."""
    if script_name == "app":
        return FileResponse(frontend_dir / "js" / "app.js", media_type="application/javascript")
    return Response(
        content="/* Migrated to CraveCart */ if ('serviceWorker' in navigator) { navigator.serviceWorker.getRegistrations().then(function(r){ for(var i=0;i<r.length;i++) r[i].unregister(); }); } if (!window.__crave_redirected) { window.__crave_redirected = true; window.location.href = '/'; }",
        media_type="application/javascript",
        headers=NO_CACHE_HEADERS,
    )



PAGE_ALIASES = {
    "admin": "admin-dashboard",
    "admin-dashboard": "admin-dashboard",
    "restaurant": "restaurant-dashboard",
    "restaurant-dashboard": "restaurant-dashboard",
    "delivery": "delivery-dashboard",
    "delivery-dashboard": "delivery-dashboard",
    "login": "login",
    "register": "register",
    "restaurants": "restaurants",
    "foods": "foods",
    "food": "food",
    "cart": "cart",
    "checkout": "checkout",
    "orders": "orders",
    "order": "order",
    "profile": "profile",
}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/{page_name}.html")
async def frontend_page_html(page_name: str):
    target = PAGE_ALIASES.get(page_name, page_name)
    page = frontend_dir / f"{target}.html"
    if not page.is_file():
        return FileResponse(frontend_dir / "index.html", status_code=404, headers=NO_CACHE_HEADERS)
    return FileResponse(page, headers=NO_CACHE_HEADERS)


@app.get("/{page_name}")
async def frontend_page_clean(page_name: str):
    target = PAGE_ALIASES.get(page_name)
    if target:
        page = frontend_dir / f"{target}.html"
        if page.is_file():
            return FileResponse(page, headers=NO_CACHE_HEADERS)
    return FileResponse(frontend_dir / "index.html", status_code=404, headers=NO_CACHE_HEADERS)
