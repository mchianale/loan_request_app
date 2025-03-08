import bcrypt
from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = "HS256"
EXPIRES_DELTA : timedelta = timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_current_date()->datetime:
    return datetime.now(timezone(timedelta(hours=1))) 


def decode_token(credentials : str)->str:
    payload = jwt.decode(credentials, os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
    return payload.get("sub")