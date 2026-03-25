from fastapi import FastAPI,HTTPException,Query,Path,Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from pydantic_model import Register_Team,Registration_Response,Login_Model,Important_Settings,Login_Admin,Admin_Response,Match_Create,Match_Response,Match_Performance_Response,Match_Performance_Create,Comment_Create,CommunityPost_Response,Comment_Response
from passlib.context import CryptContext
from jose import JWTError, jwt
from sql_models import Team,Admin,MatchPerformance,Match,Map,Map_FreeFireMax
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
import os,json

Settings = Important_Settings()

espire = FastAPI(title="Espire Platform")

@espire.get("/")
def home():
    return {"message": "Espire Plateform API running"}
from fastapi.middleware.cors import CORSMiddleware

espire.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    try:
        db= SessionLocal()
        yield db
    finally:
        db.close()

def seed_maps(db:Session):
    maps = [
        Map_FreeFireMax.Bermuda,
        Map_FreeFireMax.Purgatory,
        Map_FreeFireMax.Kalahari,
        Map_FreeFireMax.Alpine,
        Map_FreeFireMax.Nexterra,
        Map_FreeFireMax.Solara

    ]
    for particular_map in maps:
        existing_map = db.query(Map).filter(Map.name==particular_map).first()
        if not existing_map:
            db.add(Map(name=particular_map))
    db.commit()

Password_context = CryptContext(schemes=["argon2"],deprecated="auto")

def seed_admins_from_json(db: Session, file_path="admin.json"):
    try:
        with open(file_path, "r") as f:
            admins = json.load(f)
    except Exception as e:
        print(f"Error loading admin.json: {e}")
        return
    for admin_data in admins:
        id=admin_data.get("id")
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
                
                name=name,
                email=email,
                username=username,
                hash_password=hashed_password
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            # print(f"Seeded admin: {username}")


@espire.on_event("startup")
def startup_event():
    db=SessionLocal()
    seed_maps(db)
    seed_admins_from_json(db)
    db.close()
    

def get_password_hash(password):
    return Password_context.hash(password)

def verify_password(plain_password, hashed_password):
    return Password_context.verify(plain_password,hashed_password)




'''------------------------ROUTE- REGISTER TEAM------------------------------------'''

@espire.post("/registerTeam",response_model=Registration_Response)
def Team_Registration(body:Register_Team, db:Session=Depends(get_db)):

    is_teamExist= db.query(Team).filter(Team.email== body.email).first()
    if is_teamExist:
        raise HTTPException(status_code=409, detail={"message":"Email already exist"})
    is_teamExist=db.query(Team).filter(Team.team_name==body.team_name).first()
    if is_teamExist:
        raise HTTPException(status_code=409,detail={"msg":"Team already exist."})
    
    hashed_password = get_password_hash(body.password)
    year=datetime.now().strftime("%y")
    prefix = "ESP"
    last_team = db.query(Team).filter(Team.id.startswith(year+prefix)).order_by(Team.id.desc()).first()
    if last_team:
        # Extract last two digits (suffix)
        last_suffix = int(last_team.id[-2:])
        new_suffix = str(last_suffix + 1).zfill(2)
    else:
        new_suffix = "01"

    team_id = f"{year}{prefix}{new_suffix}"

    registered_team = Team(
        id=team_id,
        team_name = body.team_name,
        email= body.email,
        hash_password = hashed_password,
        
    )

    db.add(registered_team)
    db.commit()
    db.refresh(registered_team)

    return ({
        "team_id":registered_team.id,
        "team_name":registered_team.team_name,
        "email":registered_team.email
    })

'''--------------------------ROUTE- TEAM LOGIN--------------------------------------------'''

def create_access_token(data:dict):
    expire_time= datetime.now()+timedelta(minutes=Settings.Expire_Time)
    encode_data = {**data,"exp":expire_time}
    return jwt.encode(encode_data,Settings.SECRET_KEY,algorithm=Settings.ALGORITHM)

def decode_access_token(token:str):
    try:
        payload=jwt.decode(token,Settings.SECRET_KEY,algorithms=Settings.ALGORITHM)
        return payload
    except JWTError:
        return None

@espire.post("/loginTeam")
def Team_Login(body:Login_Model,db:Session=Depends(get_db)):
    is_team= db.query(Team).filter(Team.email==body.email).first()
    if not is_team:
        raise HTTPException(status_code=401,detail="Invalid email.")
    if not verify_password(body.password, is_team.hash_password):
        raise HTTPException(status_code=401,detail="Incorrect password.")
    
    token = create_access_token({"email":is_team.email, "team_name":is_team.team_name,"team_id":is_team.id})
    
    return {"token":token, "token type":"bearer",
            "msg":"Login Successful."}

team_Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="loginTeam")

def get_current_team(db:Session=Depends(get_db),token:str = Depends(team_Oauth2_scheme)):
    
    
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

@espire.get("/teamProfile")
def Team_Profile(current_team:Team=Depends(get_current_team)):
    return {"team_name":current_team.team_name,
            "id":current_team.id,
            "email":current_team.email
            }

@espire.get("/teams")
def list_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return [{"team_id": t.id, "team_name":t.team_name} for t in teams]

@espire.get("/teams/{team_id}")
def get_team(team_id:str,db:Session=Depends(get_db)):
    team = db.query(Team).filter(Team.id==team_id).first()
    if not team:
        raise HTTPException(status_code=404,detail="Team not found.")
    return {"team_id":team.id,"team_name":team.team_name}





'''--------------------LOGIN ADMIN------------------------------------'''
'''--------------------LOGIN ADMIN (FIXED)------------------------------------'''
@espire.post("/loginAdmin")
def Admin_Login(body:Login_Admin, db:Session=Depends(get_db)):
    is_admin = db.query(Admin).filter(Admin.email == body.email).first()
    if not is_admin:
        raise HTTPException(status_code=400, detail="Invalid email.")
    if not verify_password(body.password, is_admin.hash_password):
        raise HTTPException(status_code=400, detail="Incorrect Password.")
    
    # ADD name and username to the token payload here!
    token = create_access_token({
        "id":is_admin.id,
        "email": is_admin.email, 
        "name": is_admin.name, 
        "username": is_admin.username
    })
    return {"token": token, "msg": "Admin login successful."}

admin_Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="loginAdmin")

def get_current_admin(token:str=Depends(admin_Oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401,detail="Unauthorized access.")
    return payload

@espire.get("/adminProfile")
def Admin_Profile(current_admin:dict=Depends(get_current_admin)):
    return {"name":current_admin["name"],"username":current_admin["username"],"email":current_admin["email"]}


@espire.post("/createTeamMatch",response_model=Match_Response)
def create_match(body:Match_Create,db:Session=Depends(get_db),current_admin:dict=Depends(get_current_admin)):

    day = body.match_date.strftime("%d")
    month = body.match_date.strftime("%m")
    year = body.match_date.strftime("%y")
    prefix = "ESP"
    suffix = body.suffix.zfill(2)
    match_id = f"{day}{month}{prefix}{year}{suffix}"
    new_match= Match(id=match_id, match_date=body.match_date)
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    return {
        "id":new_match.id,
        "match_date":new_match.match_date,
    }


@espire.get("/allMatches")
def list_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).all()
    return [{"match_id": m.id, "match_date": m.match_date} for m in matches]


# from enum import Enum as PyEnum
from sqlalchemy import Enum

@espire.post("/createMatchPerformance", response_model=Match_Performance_Response)
def create_match_performance(body: Match_Performance_Create,db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)):
    # Create new performance record
    match_statistics = MatchPerformance(**body.dict())
    match_statistics = MatchPerformance(
    match_id=body.match_id,
    team_id=body.team_id,
    kills=body.kills,
    result=body.result,
    map_name=body.map_name.value if isinstance(body.map_name, Enum) else body.map_name,
    score=body.score
)


    db.add(match_statistics)
    db.commit()
    db.refresh(match_statistics)
    all_scores = db.query(MatchPerformance.score).filter(MatchPerformance.match_id==body.match_id).all()
    scores= [s[0] for s in all_scores]
    scores.sort()

    rank=scores.index(match_statistics.score)+1
    percentile=(rank/len(scores))*100
    conversion_10=(percentile/10)
    match_statistics.rating=round(conversion_10,3)
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
        "rating": match_statistics.rating
    }

    # return match_statistics

   
@espire.get("/watch-matchStatistics", response_model=list[Match_Performance_Response])
def watch_match_statistics(current_team: Team = Depends(get_current_team),db: Session = Depends(get_db)):
    team_statistics= (
        db.query(MatchPerformance)
        .filter(MatchPerformance.team_id == current_team.id)
        .all()
    )
    

    return team_statistics

from sqlalchemy import func

def get_match_summary(match_id:str,db:Session):

    match_exists=db.query(Match).filter(Match.id==match_id).first()
    if not match_exists:
        raise HTTPException(status_code=404,detail="Match ID not found")
    

    results=(db.query(Team.team_name,func.sum(MatchPerformance.kills).label("total_kills"),func.sum(MatchPerformance.score).label("total_score")).join(Team,Team.id==MatchPerformance.team_id).filter(MatchPerformance.match_id==match_id).group_by(Team.team_name).all())
    if not results:
        return []
    sorted_results =sorted(results,key=lambda r:(r.total_score,r.total_kills), reverse=True)
    table=[]

    for rank,row in enumerate(sorted_results,start=1):
        table.append({
            "team_name":row.team_name,
            "total_kills":int(row.total_kills),
            "total_score":float(row.total_score),
            "rank":rank
            })
    return table

from sql_models import CommunityPost,Comment
@espire.post("/community/createPost",response_model=CommunityPost_Response)
def create_poat(match_id:str,db:Session=Depends(get_db),current_admin:dict=Depends(get_current_admin)):
    table=get_match_summary(match_id,db)
    if not table:
        raise HTTPException(status_code=400,detail="Cannot create post: No performance data found for this match.")
    post = CommunityPost(match_id=match_id,table_data=table,created_by=current_admin["id"])
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@espire.get("/community/posts", response_model=list[CommunityPost_Response])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(CommunityPost).all()
    return posts

@espire.get("/community/{post_id}/comments", response_model=list[Comment_Response])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return comments


@espire.post("/community/{post_id}/team_comment", response_model=Comment_Response)
def add_team_comment(post_id: int, body: Comment_Create, db: Session = Depends(get_db), current_team: Team = Depends(get_current_team)):
    comment = Comment(post_id=post_id, team_id=current_team.id, content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@espire.post("/community/{post_id}/admin_comment", response_model=Comment_Response)
def add_admin_comment(post_id: int, body: Comment_Create, db: Session = Depends(get_db), current_admin: dict = Depends(get_current_admin)):
    comment = Comment(post_id=post_id, admin_id=current_admin["id"], content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


'''DELETION OF COMMUNITY POSTS AND COMMENT'''
import asyncio
from contextlib import asynccontextmanager

async def auto_delete_expired_posts():
    while True:
        db:Session=SessionLocal()
        try:
            cutoff=datetime.utcnow()- timedelta(hours=48)
            deleted=(
                db.query(CommunityPost).filter(CommunityPost.created_at < cutoff)
                .delete(synchronize_session=False)
            )

            db.commit()
            if deleted>0:
                print(f"Cleanup Success: Removed {deleted} expired match summaries.")
        except Exception as e:
            print(f"Cleanup Error: {e}")
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app:FastAPI):
    asyncio.create_task(auto_delete_expired_posts())
    yield
app = FastAPI(lifespan=lifespan)
