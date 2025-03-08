import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import re 

load_dotenv()

ALGORITHM = "HS256"
EXPIRES_DELTA : timedelta = timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))

# security
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict)->str:
    to_encode = data.copy()
    expire = get_current_date() + EXPIRES_DELTA
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("JWT_SECRET_KEY"), algorithm=ALGORITHM)

def decode_token(credentials : str)->str:
    payload = jwt.decode(credentials, os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
    return payload.get("sub")

# validation
def validate_username(username : str)->bool:
    return username and len(username) >= 3

def validate_password(password : str)->bool:
    return len(password) >= 6 and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password) and re.search(r"\d", password)

# other
def get_current_date()->datetime:
    return datetime.now(timezone(timedelta(hours=1))) 
