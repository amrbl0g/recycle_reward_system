from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select


# Database models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True, max_length=9)
    name: str
    points: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    price_points: int


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id_fk: int = Field(index=True, foreign_key="user.id")
    type: str  # "buy" or "recycle"
    item_name: Optional[str] = None
    points_change: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


DATABASE_URL = "sqlite:///recycle.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    # Seed default shop items if not present
    default_items = [
        ("Water", 10),
        ("Drink", 15),
        ("Can", 20),
        ("Snacks", 25),
    ]
    with Session(engine) as session:
        for name, price in default_items:
            exists = session.exec(select(Item).where(Item.name == name)).first()
            if not exists:
                session.add(Item(name=name, price_points=price))
        session.commit()


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key-change-me")

# Static and templates
templates = Jinja2Templates(directory="templates")


def get_db_session():
    with Session(engine) as session:
        yield session


def get_current_user(request: Request, db: Session) -> Optional[User]:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.exec(select(User).where(User.user_id == uid)).first()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def auth_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth.html", {"request": request})


@app.post("/signup")
def signup(request: Request, name: str = Form(...), user_id: str = Form(...), db: Session = Depends(get_db_session)):
    if not (user_id.isdigit() and len(user_id) == 9):
        raise HTTPException(status_code=400, detail="userID must be exactly 9 digits")
    existing = db.exec(select(User).where(User.user_id == user_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="userID already exists")
    user = User(name=name.strip(), user_id=user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.user_id
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/login")
def login(request: Request, user_id: str = Form(...), db: Session = Depends(get_db_session)):
    if not (user_id.isdigit() and len(user_id) == 9):
        # Render auth page with error message under Login tab
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "login_error": "Invalid userID. Please enter exactly 9 digits.", "active_tab": "login"},
            status_code=400,
        )
    user = db.exec(select(User).where(User.user_id == user_id)).first()
    if not user:
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "login_error": "User not found. Please check your userID or sign up.", "active_tab": "login"},
            status_code=404,
        )
    request.session["user_id"] = user.user_id
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db_session)):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse(url="/", status_code=302)

    items: List[Item] = db.exec(select(Item)).all()
    txs: List[Transaction] = db.exec(
        select(Transaction).where(Transaction.user_id_fk == current.id).order_by(Transaction.created_at.desc())
    ).all()

    # Ranking
    all_users: List[User] = db.exec(select(User).order_by(User.points.desc(), User.created_at.asc())).all()
    top_three = all_users[:3]
    rank = 1 + sum(1 for u in all_users if u.points > current.points)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current,
            "items": items,
            "transactions": txs,
            "top_three": top_three,
            "user_rank": rank,
        },
    )


@app.post("/buy")
def buy_item(request: Request, item_name: str = Form(...), db: Session = Depends(get_db_session)):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse(url="/", status_code=302)
    item = db.exec(select(Item).where(Item.name == item_name)).first()
    if not item:
        raise HTTPException(status_code=400, detail="Item not found")
    if current.points < item.price_points:
        raise HTTPException(status_code=400, detail="Not enough points")
    current.points -= item.price_points
    db.add(Transaction(user_id_fk=current.id, type="buy", item_name=item.name, points_change=-item.price_points))
    db.add(current)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/recycle")
def recycle_points(request: Request, points: int = Form(...), db: Session = Depends(get_db_session)):
    current = get_current_user(request, db)
    if not current:
        return RedirectResponse(url="/", status_code=302)
    if points <= 0:
        raise HTTPException(status_code=400, detail="Points must be positive")
    current.points += points
    db.add(Transaction(user_id_fk=current.id, type="recycle", item_name=None, points_change=points))
    db.add(current)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


