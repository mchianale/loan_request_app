from dotenv import load_dotenv
import os
from utils import hash_password

# Load environment variables from .env file
load_dotenv()

class PasswordManager:
    def __init__(self):
        admin_password = os.environ.get("ADMIN_PASSWORD")
        
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable is not set or empty.")

        # Hash the password securely
        try:
            self.hashed_password = hash_password(password=admin_password)
        except Exception as e:
            raise Exception(f"Failed to hash password securely: {e}")

# Singleton instance
passwordManager: PasswordManager = None

def init_passwordManager():
    """Initialize the password manager instance securely."""
    global passwordManager
    if passwordManager is None:
        try:
            passwordManager = PasswordManager()
        except Exception as e:
            raise Exception(f"Password manager initialization failed: {e}")

def get_hashed_password() -> str:
    """Retrieve the hashed password securely."""
    if passwordManager is None:
        raise Exception("PasswordManager is not initialized. Ensure `init_passwordManager()` is called at startup.")
    return passwordManager.hashed_password
