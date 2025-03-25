from fastapi import FastAPI, Depends, HTTPException, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import hashlib
import secrets
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database configuration
DATABASE_CONFIG = {
    'host': '192.168.0.110',
    'user': 'root',
    'password': 'admin',
    'database': 'recommendation_system'
}

# JWT Configuration
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # Should be in env variables in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency to get the database connection
def get_db():
    connection = None
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        if connection.is_connected():
            yield connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if connection and connection.is_connected():
            connection.close()

# Pydantic models
class User(BaseModel):
    uid: int
    name: str
    email: str
    password: str

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(db, email: str):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()

async def get_current_user(request: Request, db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        return None
    
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        return None
    
    return user

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db = Depends(get_db)
):
    cursor = db.cursor()
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        if cursor.fetchone():
            return templates.TemplateResponse("signup.html", {
                "request": request, 
                "error": "Email already registered"
            })
        
        # Create user
        hashed_password = get_password_hash(password)
        cursor.execute(
            "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        db.commit()
        
        return RedirectResponse(url="/login?registered=true", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        print(f"Database error: {e}")
        return templates.TemplateResponse("signup.html", {
            "request": request, 
            "error": "Database error occurred"
        })
    finally:
        cursor.close()

@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    registered: bool = False,
    current_user: dict = Depends(get_current_user)
):
    if current_user:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "registered": registered}
    )

@app.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db = Depends(get_db)
):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user["password"]):
        return RedirectResponse(
            url="/login?error=invalid_credentials",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        expires=1800,
    )
    return response

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("home.html", {"request": request, "user": current_user})

@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user WHERE uid = %s", (user_id,))
        result = cursor.fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        return result
    except Error as e:
        print(f"Error reading user: {e}")
        raise HTTPException(status_code=500, detail="User read error")
    finally:
        cursor.close()

@app.get("/users", response_model=list[User])
def read_users(db = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Error reading users: {e}")
        raise HTTPException(status_code=500, detail="Users read error")
    finally:
        cursor.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)