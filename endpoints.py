from fastapi import FastAPI, HTTPException, Query, Path, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal
from pydantic_model import (
    Register_Team,
    Registration_Response,
    Login_Model,
    Important_Settings,
    Login_Admin,
    Admin_Response,
    Match_Create,
    Match_Response,
    Match_Performance_Response,
    Match_Performance_Create,
    Comment_Create,
    CommunityPost_Response,
    Comment_Response,
)
from passlib.context import CryptContext
from jose import JWTError, jwt
from sql_models import (
    Team,
    Admin,
    MatchPerformance,
    Match,
    Map,
    Map_FreeFireMax,
    CommunityPost,
    Comment,
)
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import func, Enum
import os, json, asyncio

# ─── Settings ────────────────────────────────────────────────────────────────
Settings = Important_Settings()

Password_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ─── DB Helpers ──────────────────────────────────────────────────────────────
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def seed_maps(db: Session):
    maps = [
        Map_FreeFireMax.Bermuda,
        Map_FreeFireMax.Purgatory,
        Map_FreeFireMax.Kalahari,
        Map_FreeFireMax.Alpine,
        Map_FreeFireMax.Nexterra,
        Map_FreeFireMax.Solara,
    ]
    for particular_map in maps:
        existing_map = db.query(Map).filter(Map.name == particular_map).first()
        if not existing_map:
            db.add(Map(name=particular_map))
    db.commit()


def seed_admins_from_json(db: Session, file_path="admin.json"):
    try:
        with open(file_path, "r") as f:
            admins = json.load(f)
    except Exception as e:
        print(f"Error loading admin.json: {e}")
        return

    for admin_data in admins:
        id = admin_data.get("id")
        email = admin_data.get("email")
        username = admin_data.get("username")
        name = admin_data.get("name")
        password = admin_data.get("password")

        if not email or not username or not password:
            print(f"Skipping invalid admin entry: {admin_data}")
            continue

        existing_admin = db.query(Admin).filter(Admin.email == email).first()
        if not existing_admin:
            hashed_password = Password_context.hash(password)
            admin = Admin(
                name=name, email=email, username=username, hash_password=hashed_password
            )
            db.add(admin)
    db.commit()


# ─── Background task: auto-delete posts older than 48 h ──────────────────────
async def auto_delete_expired_posts():
    while True:
        db: Session = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=48)
            deleted = (
                db.query(CommunityPost)
                .filter(CommunityPost.created_at < cutoff)
                .delete(synchronize_session=False)
            )
            db.commit()
            if deleted > 0:
                print(f"Cleanup: removed {deleted} expired posts.")
        except Exception as e:
            print(f"Cleanup error: {e}")
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(3600)


# ─── Lifespan (replaces deprecated @app.on_event) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = SessionLocal()
    try:
        seed_maps(db)
        seed_admins_from_json(db)
    finally:
        db.close()

    task = asyncio.create_task(auto_delete_expired_posts())
    yield
    # Shutdown
    task.cancel()


# ─── Single FastAPI instance (FIXED: was two instances before) ────────────────
espire = FastAPI(title="Espire Platform", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
# ─── CORS (FIXED: allow_origins=["*"] + allow_credentials=True is invalid) ───
# List every origin that should be allowed. Add your frontend URL here.
ALLOWED_ORIGINS = [
    "https://espire-platform.gk2885970.replit.dev",  # Replit frontend (update if different)
    "http://localhost:3000",  # Local dev
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5500",  # VS Code Live Server
]

espire.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth helpers ─────────────────────────────────────────────────────────────
def get_password_hash(password):
    return Password_context.hash(password)


def verify_password(plain_password, hashed_password):
    return Password_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    expire_time = datetime.now() + timedelta(minutes=Settings.Expire_Time)
    encode_data = {**data, "exp": expire_time}
    return jwt.encode(encode_data, Settings.SECRET_KEY, algorithm=Settings.ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ─── OAuth2 schemes ───────────────────────────────────────────────────────────
team_Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="loginTeam")
admin_Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="loginAdmin")


def get_current_team(
    db: Session = Depends(get_db), token: str = Depends(team_Oauth2_scheme)
):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Unauthorized Access")
    team_id = payload.get("team_id")
    if team_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    return team


def get_current_admin(token: str = Depends(admin_Oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    return payload

    # ═══════════════════════════════════════════════════════════════════════════════
    #  ROUTES
    # ═══════════════════════════════════════════════════════════════════════════════

    # ── Root health check ─────────────────────────────────────────────────────────
    # --- Root Page (HTML)
    @espire.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})


# ── Register Team ─────────────────────────────────────────────────────────────
@espire.post("/registerTeam", response_model=Registration_Response)
def Team_Registration(body: Register_Team, db: Session = Depends(get_db)):
    if db.query(Team).filter(Team.email == body.email).first():
        raise HTTPException(status_code=409, detail={"message": "Email already exist"})
    if db.query(Team).filter(Team.team_name == body.team_name).first():
        raise HTTPException(status_code=409, detail={"msg": "Team already exist."})

    hashed_password = get_password_hash(body.password)
    year = datetime.now().strftime("%y")
    prefix = "ESP"

    last_team = (
        db.query(Team)
        .filter(Team.id.startswith(year + prefix))
        .order_by(Team.id.desc())
        .first()
    )
    new_suffix = str(int(last_team.id[-2:]) + 1).zfill(2) if last_team else "01"
    team_id = f"{year}{prefix}{new_suffix}"

    registered_team = Team(
        id=team_id,
        team_name=body.team_name,
        email=body.email,
        hash_password=hashed_password,
    )
    db.add(registered_team)
    db.commit()
    db.refresh(registered_team)

    return {
        "team_id": registered_team.id,
        "team_name": registered_team.team_name,
        "email": registered_team.email,
    }


# ── Team Login ────────────────────────────────────────────────────────────────
@espire.post("/loginTeam")
def Team_Login(body: Login_Model, db: Session = Depends(get_db)):
    is_team = db.query(Team).filter(Team.email == body.email).first()
    if not is_team:
        raise HTTPException(status_code=401, detail="Invalid email.")
    if not verify_password(body.password, is_team.hash_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    token = create_access_token(
        {"email": is_team.email, "team_name": is_team.team_name, "team_id": is_team.id}
    )
    return {"token": token, "token_type": "bearer", "msg": "Login Successful."}


# ── Team Profile ──────────────────────────────────────────────────────────────
@espire.get("/teamProfile")
def Team_Profile(current_team: Team = Depends(get_current_team)):
    return {
        "team_name": current_team.team_name,
        "id": current_team.id,
        "email": current_team.email,
    }


# ── List / Get Teams ──────────────────────────────────────────────────────────
@espire.get("/teams")
def list_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return [{"team_id": t.id, "team_name": t.team_name} for t in teams]


@espire.get("/teams/{team_id}")
def get_team(team_id: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    return {"team_id": team.id, "team_name": team.team_name}


# ── Admin Login ───────────────────────────────────────────────────────────────
@espire.post("/loginAdmin")
def Admin_Login(body: Login_Admin, db: Session = Depends(get_db)):
    is_admin = db.query(Admin).filter(Admin.email == body.email).first()
    if not is_admin:
        raise HTTPException(status_code=400, detail="Invalid email.")
    if not verify_password(body.password, is_admin.hash_password):
        raise HTTPException(status_code=400, detail="Incorrect Password.")

    token = create_access_token(
        {
            "id": is_admin.id,
            "email": is_admin.email,
            "name": is_admin.name,
            "username": is_admin.username,
        }
    )
    return {"token": token, "token_type": "bearer", "msg": "Admin login successful."}


# ── Admin Profile ─────────────────────────────────────────────────────────────
@espire.get("/adminProfile")
def Admin_Profile(current_admin: dict = Depends(get_current_admin)):
    return {
        "name": current_admin["name"],
        "username": current_admin["username"],
        "email": current_admin["email"],
    }


# ── Create Match ──────────────────────────────────────────────────────────────
@espire.post("/createTeamMatch", response_model=Match_Response)
def create_match(
    body: Match_Create,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    day = body.match_date.strftime("%d")
    month = body.match_date.strftime("%m")
    year = body.match_date.strftime("%y")
    prefix = "ESP"
    suffix = body.suffix.zfill(2)
    match_id = f"{day}{month}{prefix}{year}{suffix}"

    new_match = Match(id=match_id, match_date=body.match_date)
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    return {"id": new_match.id, "match_date": new_match.match_date}


# ── List Matches ──────────────────────────────────────────────────────────────
@espire.get("/allMatches")
def list_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).all()
    return [{"match_id": m.id, "match_date": m.match_date} for m in matches]


# ── Create Match Performance ──────────────────────────────────────────────────
@espire.post("/createMatchPerformance", response_model=Match_Performance_Response)
def create_match_performance(
    body: Match_Performance_Create,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    match_statistics = MatchPerformance(
        match_id=body.match_id,
        team_id=body.team_id,
        kills=body.kills,
        result=body.result,
        map_name=body.map_name.value
        if isinstance(body.map_name, Enum)
        else body.map_name,
        score=body.score,
    )
    db.add(match_statistics)
    db.commit()
    db.refresh(match_statistics)

    all_scores = (
        db.query(MatchPerformance.score)
        .filter(MatchPerformance.match_id == body.match_id)
        .all()
    )
    scores = sorted([s[0] for s in all_scores])
    rank = scores.index(match_statistics.score) + 1
    percentile = (rank / len(scores)) * 100
    match_statistics.rating = round(percentile / 10, 3)

    db.add(match_statistics)
    db.commit()
    db.refresh(match_statistics)

    team = db.query(Team).filter(Team.id == body.team_id).first()
    return {
        "match_id": match_statistics.match_id,
        "map_name": match_statistics.map_name,
        "team_id": match_statistics.team_id,
        "team_name": team.team_name if team else "Unknown",
        "kills": match_statistics.kills,
        "result": match_statistics.result,
        "score": match_statistics.score,
        "rating": match_statistics.rating,
    }


# ── Watch Match Statistics (team) ─────────────────────────────────────────────
@espire.get("/watch-matchStatistics", response_model=list[Match_Performance_Response])
def watch_match_statistics(
    current_team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    return (
        db.query(MatchPerformance)
        .filter(MatchPerformance.team_id == current_team.id)
        .all()
    )


# ─── Community helpers ────────────────────────────────────────────────────────
def get_match_summary(match_id: str, db: Session):
    if not db.query(Match).filter(Match.id == match_id).first():
        raise HTTPException(status_code=404, detail="Match ID not found")

    results = (
        db.query(
            Team.team_name,
            func.sum(MatchPerformance.kills).label("total_kills"),
            func.sum(MatchPerformance.score).label("total_score"),
        )
        .join(Team, Team.id == MatchPerformance.team_id)
        .filter(MatchPerformance.match_id == match_id)
        .group_by(Team.team_name)
        .all()
    )
    if not results:
        return []

    sorted_results = sorted(
        results, key=lambda r: (r.total_score, r.total_kills), reverse=True
    )
    return [
        {
            "team_name": row.team_name,
            "total_kills": int(row.total_kills),
            "total_score": float(row.total_score),
            "rank": rank,
        }
        for rank, row in enumerate(sorted_results, start=1)
    ]


# ── Community: Create Post ────────────────────────────────────────────────────
@espire.post("/community/createPost", response_model=CommunityPost_Response)
def create_post(
    match_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    table = get_match_summary(match_id, db)
    if not table:
        raise HTTPException(
            status_code=400,
            detail="Cannot create post: No performance data found for this match.",
        )
    post = CommunityPost(
        match_id=match_id, table_data=table, created_by=current_admin["id"]
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


# ── Community: List Posts ─────────────────────────────────────────────────────
@espire.get("/community/posts", response_model=list[CommunityPost_Response])
def list_posts(db: Session = Depends(get_db)):
    return db.query(CommunityPost).all()


# ── Community: List Comments ──────────────────────────────────────────────────
@espire.get("/community/{post_id}/comments", response_model=list[Comment_Response])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.post_id == post_id).all()


# ── Community: Team Comment ───────────────────────────────────────────────────
@espire.post("/community/{post_id}/team_comment", response_model=Comment_Response)
def add_team_comment(
    post_id: int,
    body: Comment_Create,
    db: Session = Depends(get_db),
    current_team: Team = Depends(get_current_team),
):
    comment = Comment(post_id=post_id, team_id=current_team.id, content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# ── Community: Admin Comment ──────────────────────────────────────────────────
@espire.post("/community/{post_id}/admin_comment", response_model=Comment_Response)
def add_admin_comment(
    post_id: int,
    body: Comment_Create,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    comment = Comment(
        post_id=post_id, admin_id=current_admin["id"], content=body.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
