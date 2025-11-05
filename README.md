# Recycle Rewards System

A smart recycling and reward machine web app. Users sign up with a 9-digit userID, recycle to earn points, and redeem points in the shop.

## Tech Stack
- FastAPI
- SQLModel
- SQLite
- Tailwind CSS (via CDN)

## Project Structure
- `main.py` — FastAPI app, models, routes, session auth, DB seeding
- `templates/` — HTML templates
  - `auth.html` — Login/Signup
  - `dashboard.html` — User info, points, shop, recycle, transactions, ranks
- `requirements.txt` — Python dependencies

## Prerequisites
- Python 3.10+

## Setup & Run
1. Clone or open the project folder:
```bash
cd D:\Experiments\recycle_reward_system
```

2. (Optional) Create and activate a virtual environment:
```bash
python -m venv venv
# PowerShell
venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the server (choose one):
- Using the built-in runner:
```bash
python main.py
```
- Using Uvicorn directly with auto-reload:
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

5. Open the app:
- `http://127.0.0.1:8000`

## Usage
- Signup: provide a Name and a 9-digit numeric `userID`.
- Login: enter your 9-digit `userID`.
- Dashboard:
  - See your points and rank (plus top 3 users).
  - Recycle: add points (simulating deposit).
  - Shop: buy items (Water, Drink, Can, Snacks). Buttons are disabled if you lack points.
  - Transactions: view history of purchases and recycling.
- Logout via the header link.

## Data & Seeding
- SQLite database file `recycle.db` is created on first run in the project directory.
- Shop items are seeded automatically (Water, Drink, Can, Snacks).

## Notes
- Sessions are provided by Starlette `SessionMiddleware`.
- Tailwind is loaded from CDN; no extra build is required.

## API Endpoints (overview)
- `GET /` — Auth page (login/signup)
- `POST /signup` — Create user (`name`, `user_id` = 9 digits)
- `POST /login` — Login (`user_id` = 9 digits)
- `GET /logout` — Clear session
- `GET /dashboard` — Dashboard (requires login)
- `POST /buy` — Buy an item (`item_name`)
- `POST /recycle` — Add points (`points`)

## Troubleshooting
- If you see `ModuleNotFoundError`, ensure you installed requirements: `pip install -r requirements.txt`.
- If the server runs but UI looks unstyled, check your internet connection (Tailwind via CDN).

