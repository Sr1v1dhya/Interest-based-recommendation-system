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
    'database': 'recsys'
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
        
        # Get the user ID of the newly registered user
        cursor.execute("SELECT uid FROM user WHERE email = %s", (email,))
        user_id = cursor.fetchone()[0]
        
        # Create access token for the new user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        response = RedirectResponse(url=f"/preferences?uid={user_id}", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,  # 30 minutes
            expires=1800,
        )
        return response
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
async def home(request: Request, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Check if user has preferences for each content type
    cursor = db.cursor(dictionary=True)
    user_id = current_user["uid"]
    
    try:
        # Check movie preferences
        cursor.execute("SELECT COUNT(*) as count FROM USER_MOVIE_LANG_PREF WHERE UID = %s", (user_id,))
        has_movie_lang = cursor.fetchone()["count"] > 0
        
        cursor.execute("SELECT COUNT(*) as count FROM USER_MOVIE_GEN_PREF WHERE UID = %s", (user_id,))
        has_movie_gen = cursor.fetchone()["count"] > 0
        
        has_movie_preferences = has_movie_lang or has_movie_gen  # Changed from 'and' to 'or' to support partial preferences
        movie_recommendations = []
        
        # Adjust query based on which preferences exist
        if has_movie_preferences:
            if has_movie_lang and has_movie_gen:
                # Both language and genre preferences exist
                cursor.execute("""
                    SELECT M.MID, M.MOVIE, G.GENRE, L.LANGUAGE 
                    FROM MOVIES M   
                    JOIN MOVIES_GENRES MG ON M.MID = MG.MID   
                    JOIN USER_MOVIE_GEN_PREF UMG ON MG.GID = UMG.GID   
                    JOIN USER_MOVIE_LANG_PREF UMLP ON M.LID = UMLP.LID   
                    JOIN GENRES G ON MG.GID = G.GID   
                    JOIN LANGUAGES L ON M.LID = L.LID   
                    WHERE UMG.UID = %s  
                    AND UMLP.UID = %s  
                    AND M.MID NOT IN (SELECT MID FROM USER_MOVIE_WATCHED WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id, user_id))
            elif has_movie_lang:
                # Only language preferences exist
                cursor.execute("""
                    SELECT M.MID, M.MOVIE, G.GENRE, L.LANGUAGE 
                    FROM MOVIES M
                    JOIN MOVIES_GENRES MG ON M.MID = MG.MID
                    JOIN GENRES G ON MG.GID = G.GID
                    JOIN LANGUAGES L ON M.LID = L.LID
                    JOIN USER_MOVIE_LANG_PREF UMLP ON M.LID = UMLP.LID
                    WHERE UMLP.UID = %s
                    AND M.MID NOT IN (SELECT MID FROM USER_MOVIE_WATCHED WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id))
            elif has_movie_gen:
                # Only genre preferences exist
                cursor.execute("""
                    SELECT M.MID, M.MOVIE, G.GENRE, L.LANGUAGE 
                    FROM MOVIES M
                    JOIN MOVIES_GENRES MG ON M.MID = MG.MID
                    JOIN GENRES G ON MG.GID = G.GID
                    JOIN LANGUAGES L ON M.LID = L.LID
                    JOIN USER_MOVIE_GEN_PREF UMG ON MG.GID = UMG.GID
                    WHERE UMG.UID = %s
                    AND M.MID NOT IN (SELECT MID FROM USER_MOVIE_WATCHED WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id))
            
            movie_recommendations = cursor.fetchall()
        
        # Similarly adjust the book preferences logic
        cursor.execute("SELECT COUNT(*) as count FROM USER_BOOK_LANG_PREF WHERE UID = %s", (user_id,))
        has_book_lang = cursor.fetchone()["count"] > 0
        
        cursor.execute("SELECT COUNT(*) as count FROM USER_BOOK_GEN_PREF WHERE UID = %s", (user_id,))
        has_book_gen = cursor.fetchone()["count"] > 0
        
        has_book_preferences = has_book_lang or has_book_gen  # Changed from 'and' to 'or'
        book_recommendations = []
        
        if has_book_preferences:
            if has_book_lang and has_book_gen:
                cursor.execute("""
                    SELECT B.BID, B.BOOK, G.GENRE, L.LANGUAGE 
                    FROM BOOKS B   
                    JOIN BOOKS_GENRES BG ON B.BID = BG.BID   
                    JOIN USER_BOOK_GEN_PREF UBG ON BG.GID = UBG.GID   
                    JOIN USER_BOOK_LANG_PREF UBLP ON B.LID = UBLP.LID   
                    JOIN GENRES G ON BG.GID = G.GID   
                    JOIN LANGUAGES L ON B.LID = L.LID   
                    WHERE UBG.UID = %s  
                    AND UBLP.UID = %s  
                    AND B.BID NOT IN (SELECT BID FROM USER_BOOK_READ WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id, user_id))
            elif has_book_lang:
                cursor.execute("""
                    SELECT B.BID, B.BOOK, G.GENRE, L.LANGUAGE 
                    FROM BOOKS B
                    JOIN BOOKS_GENRES BG ON B.BID = BG.BID
                    JOIN GENRES G ON BG.GID = G.GID
                    JOIN LANGUAGES L ON B.LID = L.LID
                    JOIN USER_BOOK_LANG_PREF UBLP ON B.LID = UBLP.LID
                    WHERE UBLP.UID = %s
                    AND B.BID NOT IN (SELECT BID FROM USER_BOOK_READ WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id))
            elif has_book_gen:
                cursor.execute("""
                    SELECT B.BID, B.BOOK, G.GENRE, L.LANGUAGE 
                    FROM BOOKS B
                    JOIN BOOKS_GENRES BG ON B.BID = BG.BID
                    JOIN GENRES G ON BG.GID = G.GID
                    JOIN LANGUAGES L ON B.LID = L.LID
                    JOIN USER_BOOK_GEN_PREF UBG ON BG.GID = UBG.GID
                    WHERE UBG.UID = %s
                    AND B.BID NOT IN (SELECT BID FROM USER_BOOK_READ WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id))
            
            book_recommendations = cursor.fetchall()
        
        # And the same for TV shows
        cursor.execute("SELECT COUNT(*) as count FROM USER_TVSHOW_LANG_PREF WHERE UID = %s", (user_id,))
        has_tvshow_lang = cursor.fetchone()["count"] > 0
        
        cursor.execute("SELECT COUNT(*) as count FROM USER_TVSHOW_GEN_PREF WHERE UID = %s", (user_id,))
        has_tvshow_gen = cursor.fetchone()["count"] > 0
        
        has_tvshow_preferences = has_tvshow_lang or has_tvshow_gen  # Changed from 'and' to 'or'
        tvshow_recommendations = []
        
        if has_tvshow_preferences:
            if has_tvshow_lang and has_tvshow_gen:
                cursor.execute("""
                    SELECT T.TVID, T.TVSHOW, G.GENRE, L.LANGUAGE 
                    FROM TVSHOWS T   
                    JOIN TVSHOWS_GENRES TG ON T.TVID = TG.TVID   
                    JOIN USER_TVSHOW_GEN_PREF UTG ON TG.GID = UTG.GID   
                    JOIN USER_TVSHOW_LANG_PREF UTLP ON T.LID = UTLP.LID   
                    JOIN GENRES G ON TG.GID = G.GID   
                    JOIN LANGUAGES L ON T.LID = L.LID   
                    WHERE UTG.UID = %s  
                    AND UTLP.UID = %s  
                    AND T.TVID NOT IN (SELECT TVID FROM USER_TVSHOW_WATCHED WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id, user_id))
            elif has_tvshow_lang:
                cursor.execute("""
                    SELECT T.TVID, T.TVSHOW, G.GENRE, L.LANGUAGE 
                    FROM TVSHOWS T
                    JOIN TVSHOWS_GENRES TG ON T.TVID = TG.TVID
                    JOIN GENRES G ON TG.GID = G.GID
                    JOIN LANGUAGES L ON T.LID = L.LID
                    JOIN USER_TVSHOW_LANG_PREF UTLP ON T.LID = UTLP.LID
                    WHERE UTLP.UID = %s
                    AND T.TVID NOT IN (SELECT TVID FROM USER_TVSHOW_WATCHED WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id))
            elif has_tvshow_gen:
                cursor.execute("""
                    SELECT T.TVID, T.TVSHOW, G.GENRE, L.LANGUAGE 
                    FROM TVSHOWS T
                    JOIN TVSHOWS_GENRES TG ON T.TVID = TG.TVID
                    JOIN GENRES G ON TG.GID = G.GID
                    JOIN LANGUAGES L ON T.LID = L.LID
                    JOIN USER_TVSHOW_GEN_PREF UTG ON TG.GID = UTG.GID
                    WHERE UTG.UID = %s
                    AND T.TVID NOT IN (SELECT TVID FROM USER_TVSHOW_WATCHED WHERE UID = %s)
                    LIMIT 10
                """, (user_id, user_id))
            
            tvshow_recommendations = cursor.fetchall()
        
        # Get social connection data
        # 1. Get followers (users who follow the current user)
        cursor.execute("""
            SELECT u.uid, u.name, u.email 
            FROM user u
            JOIN FOLLOW f ON u.uid = f.XID
            WHERE f.YID = %s
        """, (user_id,))
        followers = cursor.fetchall()
        
        # 2. Get following (users whom the current user follows)
        cursor.execute("""
            SELECT u.uid, u.name, u.email 
            FROM user u
            JOIN FOLLOW f ON u.uid = f.YID
            WHERE f.XID = %s
        """, (user_id,))
        following = cursor.fetchall()
        
        # 3. Get suggestions (users who the current user doesn't follow yet)
        cursor.execute("""
            SELECT u.uid, u.name, u.email 
            FROM user u
            WHERE u.uid != %s
            AND u.uid NOT IN (
                SELECT YID FROM FOLLOW WHERE XID = %s
            )
            LIMIT 5
        """, (user_id, user_id))
        suggestions = cursor.fetchall()
        
        # 4. Get activity statistics
        cursor.execute("SELECT COUNT(*) as count FROM USER_MOVIE_WATCHED WHERE UID = %s", (user_id,))
        movies_watched = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM USER_BOOK_READ WHERE UID = %s", (user_id,))
        books_read = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM USER_TVSHOW_WATCHED WHERE UID = %s", (user_id,))
        tvshows_watched = cursor.fetchone()["count"]
        
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "user": current_user,
            "has_movie_preferences": has_movie_preferences,
            "has_book_preferences": has_book_preferences,
            "has_tvshow_preferences": has_tvshow_preferences,
            "has_movie_lang": has_movie_lang,
            "has_movie_gen": has_movie_gen,
            "has_book_lang": has_book_lang,
            "has_book_gen": has_book_gen,
            "has_tvshow_lang": has_tvshow_lang,
            "has_tvshow_gen": has_tvshow_gen,
            "movie_recommendations": movie_recommendations,
            "book_recommendations": book_recommendations,
            "tvshow_recommendations": tvshow_recommendations,
            "followers": followers,
            "following": following,
            "suggestions": suggestions,
            "movies_watched": movies_watched,
            "books_read": books_read,
            "tvshows_watched": tvshows_watched
        })
    except Error as e:
        print(f"Error loading home page data: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "user": current_user,
            "has_movie_preferences": False,
            "has_book_preferences": False,
            "has_tvshow_preferences": False,
            "has_movie_lang": False,
            "has_movie_gen": False,
            "has_book_lang": False,
            "has_book_gen": False,
            "has_tvshow_lang": False,
            "has_tvshow_gen": False,
            "movie_recommendations": [],
            "book_recommendations": [],
            "tvshow_recommendations": [],
            "followers": [],
            "following": [],
            "suggestions": [],
            "movies_watched": 0,
            "books_read": 0,
            "tvshows_watched": 0
        })
    finally:
        cursor.close()

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

# New routes for preferences
@app.get("/preferences", response_class=HTMLResponse)
async def preferences_page(request: Request, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get languages and genres from database
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM LANGUAGES")
        languages = cursor.fetchall()
        
        cursor.execute("SELECT * FROM GENRES")
        genres = cursor.fetchall()
        
        return templates.TemplateResponse("preferences.html", {
            "request": request, 
            "user": current_user,
            "languages": languages,
            "genres": genres
        })
    except Error as e:
        print(f"Error fetching preferences data: {e}")
        raise HTTPException(status_code=500, detail="Error fetching preferences data")
    finally:
        cursor.close()

@app.post("/save-preferences", response_class=HTMLResponse)
async def save_preferences(
    request: Request,
    db = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    
    try:
        # Get form data directly from request
        form = await request.form()
        
        # Extract multiple values for each preference
        movie_languages = form.getlist("movie_languages")
        movie_genres = form.getlist("movie_genres")
        book_languages = form.getlist("book_languages")
        book_genres = form.getlist("book_genres")
        tvshow_languages = form.getlist("tvshow_languages")
        tvshow_genres = form.getlist("tvshow_genres")
        
        # Filter out empty values
        movie_languages = [lang for lang in movie_languages if lang]
        movie_genres = [genre for genre in movie_genres if genre]
        book_languages = [lang for lang in book_languages if lang]
        book_genres = [genre for genre in book_genres if genre]
        tvshow_languages = [lang for lang in tvshow_languages if lang]
        tvshow_genres = [genre for genre in tvshow_genres if genre]
        
        # Debug log
        print(f"Saving preferences for user {user_id}:")
        print(f"Movie languages: {movie_languages}")
        print(f"Movie genres: {movie_genres}")
        print(f"Book languages: {book_languages}")
        print(f"Book genres: {book_genres}")
        print(f"TV Show languages: {tvshow_languages}")
        print(f"TV Show genres: {tvshow_genres}")
        
        cursor = db.cursor()
        
        # Clear existing preferences for this user
        tables = [
            "USER_MOVIE_LANG_PREF", "USER_MOVIE_GEN_PREF",
            "USER_BOOK_LANG_PREF", "USER_BOOK_GEN_PREF",
            "USER_TVSHOW_LANG_PREF", "USER_TVSHOW_GEN_PREF"
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE UID = %s", (user_id,))
        
        # Save movie preferences
        for lang_id in movie_languages:
            if lang_id:  # Skip empty values
                cursor.execute("INSERT INTO USER_MOVIE_LANG_PREF (UID, LID) VALUES (%s, %s)", 
                              (user_id, int(lang_id)))
        
        for genre_id in movie_genres:
            if genre_id:  # Skip empty values
                cursor.execute("INSERT INTO USER_MOVIE_GEN_PREF (UID, GID) VALUES (%s, %s)", 
                              (user_id, int(genre_id)))
        
        # Save book preferences
        for lang_id in book_languages:
            if lang_id:  # Skip empty values
                cursor.execute("INSERT INTO USER_BOOK_LANG_PREF (UID, LID) VALUES (%s, %s)", 
                              (user_id, int(lang_id)))
        
        for genre_id in book_genres:
            if genre_id:  # Skip empty values
                cursor.execute("INSERT INTO USER_BOOK_GEN_PREF (UID, GID) VALUES (%s, %s)", 
                              (user_id, int(genre_id)))
        
        # Save TV show preferences
        for lang_id in tvshow_languages:
            if lang_id:  # Skip empty values
                cursor.execute("INSERT INTO USER_TVSHOW_LANG_PREF (UID, LID) VALUES (%s, %s)", 
                              (user_id, int(lang_id)))
        
        for genre_id in tvshow_genres:
            if genre_id:  # Skip empty values
                cursor.execute("INSERT INTO USER_TVSHOW_GEN_PREF (UID, GID) VALUES (%s, %s)", 
                              (user_id, int(genre_id)))
        
        db.commit()
        
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        if 'cursor' in locals() and cursor:
            db.rollback()
        print(f"Error saving preferences: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <title>Error</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body class="bg-light">
                    <div class="container py-5">
                        <div class="p-5 mb-4 bg-white rounded-3 shadow">
                            <h1 class="display-5 fw-bold text-danger">An Error Occurred</h1>
                            <p class="fs-4">There was a problem saving your preferences.</p>
                            <p>Error details: {str(e)}</p>
                            <div class="mt-4">
                                <a href="/preferences" class="btn btn-primary">Try Again</a>
                                <a href="/home" class="btn btn-secondary ms-2">Go to Home</a>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """,
            status_code=500
        )

@app.get("/manage-preferences", response_class=HTMLResponse)
async def manage_preferences(request: Request, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get languages and genres
        cursor.execute("SELECT * FROM LANGUAGES")
        languages = cursor.fetchall()
        
        cursor.execute("SELECT * FROM GENRES")
        genres = cursor.fetchall()
        
        # Get user's existing preferences
        # Movie language preferences
        cursor.execute("SELECT LID FROM USER_MOVIE_LANG_PREF WHERE UID = %s", (user_id,))
        movie_lang_prefs = [row["LID"] for row in cursor.fetchall()]
        
        # Movie genre preferences
        cursor.execute("SELECT GID FROM USER_MOVIE_GEN_PREF WHERE UID = %s", (user_id,))
        movie_genre_prefs = [row["GID"] for row in cursor.fetchall()]
        
        # Book language preferences
        cursor.execute("SELECT LID FROM USER_BOOK_LANG_PREF WHERE UID = %s", (user_id,))
        book_lang_prefs = [row["LID"] for row in cursor.fetchall()]
        
        # Book genre preferences
        cursor.execute("SELECT GID FROM USER_BOOK_GEN_PREF WHERE UID = %s", (user_id,))
        book_genre_prefs = [row["GID"] for row in cursor.fetchall()]
        
        # TV Show language preferences
        cursor.execute("SELECT LID FROM USER_TVSHOW_LANG_PREF WHERE UID = %s", (user_id,))
        tvshow_lang_prefs = [row["LID"] for row in cursor.fetchall()]
        
        # TV Show genre preferences
        cursor.execute("SELECT GID FROM USER_TVSHOW_GEN_PREF WHERE UID = %s", (user_id,))
        tvshow_genre_prefs = [row["GID"] for row in cursor.fetchall()]
        
        return templates.TemplateResponse("manage_preferences.html", {
            "request": request,
            "user": current_user,
            "languages": languages,
            "genres": genres,
            "movie_lang_prefs": movie_lang_prefs,
            "movie_genre_prefs": movie_genre_prefs,
            "book_lang_prefs": book_lang_prefs,
            "book_genre_prefs": book_genre_prefs,
            "tvshow_lang_prefs": tvshow_lang_prefs,
            "tvshow_genre_prefs": tvshow_genre_prefs
        })
    except Error as e:
        print(f"Error fetching user preferences: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user preferences")
    finally:
        cursor.close()

@app.get("/manage-history", response_class=HTMLResponse)
async def manage_history(request: Request, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get watched movies with details
        cursor.execute("""
            SELECT m.MID, m.MOVIE, g.GENRE, l.LANGUAGE
            FROM MOVIES m
            JOIN USER_MOVIE_WATCHED umw ON m.MID = umw.MID
            JOIN MOVIES_GENRES mg ON m.MID = mg.MID
            JOIN GENRES g ON mg.GID = g.GID
            JOIN LANGUAGES l ON m.LID = l.LID
            WHERE umw.UID = %s
        """, (user_id,))
        movies_watched = cursor.fetchall()
        
        # Get read books with details
        cursor.execute("""
            SELECT b.BID, b.BOOK, g.GENRE, l.LANGUAGE
            FROM BOOKS b
            JOIN USER_BOOK_READ ubr ON b.BID = ubr.BID
            JOIN BOOKS_GENRES bg ON b.BID = bg.BID
            JOIN GENRES g ON bg.GID = g.GID
            JOIN LANGUAGES l ON b.LID = l.LID
            WHERE ubr.UID = %s
        """, (user_id,))
        books_read = cursor.fetchall()
        
        # Get watched TV shows with details
        cursor.execute("""
            SELECT t.TVID, t.TVSHOW, g.GENRE, l.LANGUAGE
            FROM TVSHOWS t
            JOIN USER_TVSHOW_WATCHED utw ON t.TVID = utw.TVID
            JOIN TVSHOWS_GENRES tg ON t.TVID = tg.TVID
            JOIN GENRES g ON tg.GID = g.GID
            JOIN LANGUAGES l ON t.LID = l.LID
            WHERE utw.UID = %s
        """, (user_id,))
        tvshows_watched = cursor.fetchall()
        
        return templates.TemplateResponse("history.html", {
            "request": request,
            "user": current_user,
            "movies_watched": movies_watched,
            "books_read": books_read,
            "tvshows_watched": tvshows_watched
        })
    except Error as e:
        print(f"Error fetching user history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user history")
    finally:
        cursor.close()

@app.get("/search-movies")
async def search_movies(term: str, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT m.MID, m.MOVIE, g.GENRE, l.LANGUAGE
            FROM MOVIES m
            JOIN MOVIES_GENRES mg ON m.MID = mg.MID
            JOIN GENRES g ON mg.GID = g.GID
            JOIN LANGUAGES l ON m.LID = l.LID
            WHERE m.MOVIE LIKE %s
            LIMIT 10
        """, (f"%{term}%",))
        
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Error searching movies: {e}")
        raise HTTPException(status_code=500, detail="Error searching movies")
    finally:
        cursor.close()

@app.get("/search-books")
async def search_books(term: str, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT b.BID, b.BOOK, g.GENRE, l.LANGUAGE
            FROM BOOKS b
            JOIN BOOKS_GENRES bg ON b.BID = bg.BID
            JOIN GENRES g ON bg.GID = g.GID
            JOIN LANGUAGES l ON b.LID = l.LID
            WHERE b.BOOK LIKE %s
            LIMIT 10
        """, (f"%{term}%",))
        
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Error searching books: {e}")
        raise HTTPException(status_code=500, detail="Error searching books")
    finally:
        cursor.close()

@app.get("/search-tvshows")
async def search_tvshows(term: str, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT t.TVID, t.TVSHOW, g.GENRE, l.LANGUAGE
            FROM TVSHOWS t
            JOIN TVSHOWS_GENRES tg ON t.TVID = tg.TVID
            JOIN GENRES g ON tg.GID = g.GID
            JOIN LANGUAGES l ON t.LID = l.LID
            WHERE t.TVSHOW LIKE %s
            LIMIT 10
        """, (f"%{term}%",))
        
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Error searching TV shows: {e}")
        raise HTTPException(status_code=500, detail="Error searching TV shows")
    finally:
        cursor.close()

@app.post("/add-movie-history/{movie_id}", response_class=HTMLResponse)
async def add_movie_history(
    movie_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor()
    
    try:
        # Check if already in history
        cursor.execute("SELECT * FROM USER_MOVIE_WATCHED WHERE UID = %s AND MID = %s", (user_id, movie_id))
        if cursor.fetchone():
            # Already in history, do nothing
            pass
        else:
            # Add to history
            cursor.execute("INSERT INTO USER_MOVIE_WATCHED (UID, MID) VALUES (%s, %s)", (user_id, movie_id))
            db.commit()
        
        return RedirectResponse(url="/manage-history", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        db.rollback()
        print(f"Error adding movie to history: {e}")
        raise HTTPException(status_code=500, detail="Error adding movie to history")
    finally:
        cursor.close()

@app.post("/add-book-history/{book_id}", response_class=HTMLResponse)
async def add_book_history(
    book_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor()
    
    try:
        # Check if already in history
        cursor.execute("SELECT * FROM USER_BOOK_READ WHERE UID = %s AND BID = %s", (user_id, book_id))
        if cursor.fetchone():
            # Already in history, do nothing
            pass
        else:
            # Add to history
            cursor.execute("INSERT INTO USER_BOOK_READ (UID, BID) VALUES (%s, %s)", (user_id, book_id))
            db.commit()
        
        return RedirectResponse(url="/manage-history", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        db.rollback()
        print(f"Error adding book to history: {e}")
        raise HTTPException(status_code=500, detail="Error adding book to history")
    finally:
        cursor.close()

@app.post("/add-tvshow-history/{tvshow_id}", response_class=HTMLResponse)
async def add_tvshow_history(
    tvshow_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor()
    
    try:
        # Check if already in history
        cursor.execute("SELECT * FROM USER_TVSHOW_WATCHED WHERE UID = %s AND TVID = %s", (user_id, tvshow_id))
        if cursor.fetchone():
            # Already in history, do nothing
            pass
        else:
            # Add to history
            cursor.execute("INSERT INTO USER_TVSHOW_WATCHED (UID, TVID) VALUES (%s, %s)", (user_id, tvshow_id))
            db.commit()
        
        return RedirectResponse(url="/manage-history", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        db.rollback()
        print(f"Error adding TV show to history: {e}")
        raise HTTPException(status_code=500, detail="Error adding TV show to history")
    finally:
        cursor.close()

@app.post("/remove-movie-history/{movie_id}", response_class=HTMLResponse)
async def remove_movie_history(
    movie_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor()
    
    try:
        cursor.execute("DELETE FROM USER_MOVIE_WATCHED WHERE UID = %s AND MID = %s", (user_id, movie_id))
        db.commit()
        
        return RedirectResponse(url="/manage-history", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        db.rollback()
        print(f"Error removing movie from history: {e}")
        raise HTTPException(status_code=500, detail="Error removing movie from history")
    finally:
        cursor.close()

@app.post("/remove-book-history/{book_id}", response_class=HTMLResponse)
async def remove_book_history(
    book_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor()
    
    try:
        cursor.execute("DELETE FROM USER_BOOK_READ WHERE UID = %s AND BID = %s", (user_id, book_id))
        db.commit()
        
        return RedirectResponse(url="/manage-history", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        db.rollback()
        print(f"Error removing book from history: {e}")
        raise HTTPException(status_code=500, detail="Error removing book from history")
    finally:
        cursor.close()

@app.post("/remove-tvshow-history/{tvshow_id}", response_class=HTMLResponse)
async def remove_tvshow_history(
    tvshow_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor()
    
    try:
        cursor.execute("DELETE FROM USER_TVSHOW_WATCHED WHERE UID = %s AND TVID = %s", (user_id, tvshow_id))
        db.commit()
        
        return RedirectResponse(url="/manage-history", status_code=status.HTTP_303_SEE_OTHER)
    except Error as e:
        db.rollback()
        print(f"Error removing TV show from history: {e}")
        raise HTTPException(status_code=500, detail="Error removing TV show from history")
    finally:
        cursor.close()

@app.get("/connections", response_class=HTMLResponse)
async def connections_page(request: Request, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get followers with their stats and check if current user follows them back
        cursor.execute("""
            SELECT u.uid, u.name, u.email,
            (SELECT COUNT(*) FROM FOLLOW WHERE XID = u.uid) as follower_count,
            (SELECT COUNT(*) FROM FOLLOW WHERE YID = u.uid) as following_count,
            EXISTS(SELECT 1 FROM FOLLOW WHERE XID = %s AND YID = u.uid) as is_following
            FROM user u
            JOIN FOLLOW f ON u.uid = f.XID
            WHERE f.YID = %s
        """, (user_id, user_id))
        followers = cursor.fetchall()
        
        # Get users the current user follows
        cursor.execute("""
            SELECT u.uid, u.name, u.email,
            (SELECT COUNT(*) FROM FOLLOW WHERE XID = u.uid) as follower_count,
            (SELECT COUNT(*) FROM FOLLOW WHERE YID = u.uid) as following_count
            FROM user u
            JOIN FOLLOW f ON u.uid = f.YID
            WHERE f.XID = %s
        """, (user_id,))
        following = cursor.fetchall()
        
        # Get suggestions (users not followed by current user)
        cursor.execute("""
            SELECT u.uid, u.name, u.email,
            (SELECT COUNT(*) FROM FOLLOW WHERE XID = u.uid) as follower_count,
            (SELECT COUNT(*) FROM FOLLOW WHERE YID = u.uid) as following_count
            FROM user u
            WHERE u.uid != %s
            AND u.uid NOT IN (
                SELECT YID FROM FOLLOW WHERE XID = %s
            )
            LIMIT 10
        """, (user_id, user_id))
        suggestions = cursor.fetchall()
        
        return templates.TemplateResponse("connections.html", {
            "request": request,
            "user": current_user,
            "followers": followers,
            "following": following,
            "suggestions": suggestions
        })
    
    except Error as e:
        print(f"Error loading connections page: {e}")
        raise HTTPException(status_code=500, detail="Error loading connections data")
    finally:
        cursor.close()

@app.post("/follow/{target_id}", response_class=HTMLResponse)
async def follow_user(
    request: Request,
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    cursor = db.cursor()
    try:
        # Check if already following
        cursor.execute("SELECT * FROM FOLLOW WHERE XID = %s AND YID = %s", (user_id, target_id))
        if cursor.fetchone():
            # Already following, do nothing
            pass
        else:
            # Follow the user
            cursor.execute("INSERT INTO FOLLOW (XID, YID) VALUES (%s, %s)", (user_id, target_id))
            db.commit()
        
        # Return to previous page
        referer = request.headers.get("referer", "/connections")
        return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    
    except Error as e:
        db.rollback()
        print(f"Error following user: {e}")
        raise HTTPException(status_code=500, detail="Error following user")
    finally:
        cursor.close()

@app.post("/unfollow/{target_id}", response_class=HTMLResponse)
async def unfollow_user(
    request: Request,
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_id = current_user["uid"]
    
    cursor = db.cursor()
    try:
        # Unfollow the user
        cursor.execute("DELETE FROM FOLLOW WHERE XID = %s AND YID = %s", (user_id, target_id))
        db.commit()
        
        # Return to previous page
        referer = request.headers.get("referer", "/connections")
        return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    
    except Error as e:
        db.rollback()
        print(f"Error unfollowing user: {e}")
        raise HTTPException(status_code=500, detail="Error unfollowing user")
    finally:
        cursor.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)