from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import os
import json

from . import models, schemas, database, crud

# --- Load .env values ---
load_dotenv()
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASS")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGORITHM = "HS256"

# --- Initialize App ---
app = FastAPI()
models.Base.metadata.create_all(bind=database.engine)
logging.basicConfig(filename="app.log", level=logging.INFO)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependency: Get DB Session ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- JWT Auth helpers ---
def create_token(data: dict, expires_delta=timedelta(hours=12)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing or invalid")
    return decode_token(auth_header.split(" ")[1])

def require_role(role: str):
    def wrapper(user=Depends(get_current_user)):
        if user.get("role") != role and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return wrapper

# --- Login Endpoint ---
@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if form.username == ADMIN_USER and form.password == ADMIN_PASSWORD:
        token = create_token({"sub": form.username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}

    # Simulated domain user login (replace with LDAP if needed)
    if form.username.startswith("agent_"):
        token = create_token({"sub": form.username, "role": "agent"})
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- Public: Create Request ---
@app.post("/requests", response_model=schemas.Request)
def create_request(request: schemas.RequestCreate, db: Session = Depends(get_db)):
    logging.info(f"New request: {request}")
    return crud.create_request(db, request)

# --- Protected: Review Requests ---
@app.get("/requests", response_model=list[schemas.Request])
def read_requests(db: Session = Depends(get_db), user=Depends(require_role("agent"))):
    return crud.get_requests(db)

@app.post("/requests/{request_id}/approve")
def approve_request(request_id: int, db: Session = Depends(get_db), user=Depends(require_role("agent"))):
    crud.update_status(db, request_id, "approved")
    logging.info(f"Approved request ID {request_id}")
    return {"message": "Approved"}

@app.post("/requests/{request_id}/deny")
def deny_request(request_id: int, db: Session = Depends(get_db), user=Depends(require_role("agent"))):
    crud.update_status(db, request_id, "denied")
    logging.info(f"Denied request ID {request_id}")
    return {"message": "Denied"}

# --- Admin Panel Settings ---
@app.get("/admin/settings")
def get_settings(user=Depends(require_role("admin"))):
    with open("app/settings.json") as f:
        return json.load(f)

@app.post("/admin/settings")
def update_settings(new_settings: dict, user=Depends(require_role("admin"))):
    with open("app/settings.json", "w") as f:
        json.dump(new_settings, f, indent=2)
    logging.info("Updated settings")
    return {"message": "Settings updated"}
