from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

REQUIRED_PAGES = {
    "index.html",
    "login.html",
    "register.html",
    "restaurants.html",
    "restaurant.html",
    "foods.html",
    "food.html",
    "cart.html",
    "checkout.html",
    "orders.html",
    "order.html",
    "profile.html",
    "restaurant-dashboard.html",
    "delivery-dashboard.html",
    "admin-dashboard.html",
}


def test_frontend_has_only_the_required_shared_assets_and_pages():
    assert {path.name for path in FRONTEND_ROOT.glob("*.html")} == REQUIRED_PAGES
    assert (FRONTEND_ROOT / "css" / "style.css").is_file()
    assert (FRONTEND_ROOT / "js" / "app.js").is_file()
    assert not list(FRONTEND_ROOT.glob("package*.json"))
    assert not (FRONTEND_ROOT / "vite.config.js").exists()
    assert not (FRONTEND_ROOT / "src").exists()
    assert not (FRONTEND_ROOT / "dist").exists()


def test_root_launcher_does_not_require_node_or_start_a_second_server():
    launcher = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert "uvicorn" in launcher
    assert "vite" not in launcher.lower()
    assert "node_modules" not in launcher
    assert "localhost:3000" not in launcher


def test_fastapi_root_serves_html_frontend():
    main_source = (PROJECT_ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert "FileResponse" in main_source
    assert "frontend" in main_source
