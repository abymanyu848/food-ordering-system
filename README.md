# Food Ordering Management System

A simple, submission-ready UG mini project for browsing restaurants, ordering food, and administering a food-ordering service.

## Technology stack

- Frontend: HTML, CSS and vanilla JavaScript
- Backend: Python, FastAPI and Uvicorn
- Database: SQLite (`backend/food_ordering.db`)
- ORM: SQLAlchemy
- Authentication: JWT with bcrypt password hashing

No Docker, PostgreSQL, Node.js, React, Vite, TypeScript, or Tailwind CSS is required.

## Requirements

- Python 3.10 or later

## Run the application

Option A — double-click `run.bat`. It creates/uses `.venv`, installs
`requirements.txt`, seeds demo data, and starts the app.

Option B — open a terminal in the project folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python backend\seed.py
python main.py
```

The complete application starts at `http://127.0.0.1:8000`. FastAPI serves the HTML, CSS and JavaScript directly. API documentation is available at `http://127.0.0.1:8000/docs`.

FastAPI automatically creates all SQLite tables when it starts. The seed command adds the demonstration data only when the database is empty (and upgrades legacy demo passwords to bcrypt hashes when needed).

## Configuration

Copy `.env.example` to `.env` when running outside local development and replace
the placeholder `SECRET_KEY` with a long, random value. Keep `.env` local; it is
ignored by Git and must never contain credentials committed to the repository.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Administrator | `admin@example.com` | `admin123` |
| Customer | `john@example.com` | `password123` |
| Restaurant | `restaurant1@example.com` | `restaurant123` |
| Delivery | `delivery1@example.com` | `delivery123` |

## Demo Data Note

Restaurant names and selected menu-item names are based on publicly available
restaurant listings and menus for Nagercoil. Prices in the demo database are
illustrative unless explicitly identified as publicly listed prices. Menus and
prices may change over time.

## Features

### Customer
- Registration, login, JWT authentication, and profile management
- Restaurant browsing with search, ratings, and category filters
- Food browsing, search, availability filtering, and price sorting
- Single-restaurant cart with dynamic quantity adjustments
- Cash on Delivery (COD) checkout with delivery address selection
- Live order history, tracking, and cancellation for pending orders
- Restaurant and dish reviews and ratings

### Restaurant
- Dedicated restaurant partner dashboard
- Restaurant profile management (operating hours, description, contact)
- Live order queue (Pending, Accepted, Preparing, Ready)
- Menu item management (add dish, edit prices, upload food photos, toggle availability)

### Delivery
- Dedicated delivery personnel dashboard
- View assigned active delivery tasks with customer and restaurant details
- Update delivery statuses (Picked up, In transit, Delivered)
- View past delivery history and completed runs

### Admin
- Unified administration dashboard with operational metrics
- User account management (role assignments, activation/deactivation)
- Restaurant and branch management
- Category and global menu item administration
- System-wide order oversight and status overrides

## Running Tests

To run the automated backend test suite:

```powershell
# In PowerShell:
$env:PYTHONPATH="backend"
pytest backend/tests
```

Or using the virtual environment:

```powershell
.\.venv\Scripts\python -m pytest backend/tests
```

## Project structure

```text
backend/             FastAPI application, API routes, models, database schemas, and seed script
backend/uploads/     Static image assets for restaurants and menu dishes
frontend/            Multi-page HTML frontend templates, CSS design tokens/styles, and client app JS
frontend/css/        Global styles and design system (style.css)
frontend/js/         Client application logic and API communication (app.js)
main.py              Root application launcher (starts FastAPI server with Uvicorn)
run.bat              One-click Windows setup and launch script
requirements.txt     Python dependencies
```

