from dotenv import load_dotenv
import os

def load_config():
    load_dotenv()
    
# Automatically load when this module is imported
load_config()

# MongoDB configurations
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_db")

# Collection names
USERS_COLLECTION = "users"
CHECKPOINTS_COLLECTION = "checkpoints"

# Auth settings
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-dev-only") # Should be replaced in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

# Global settings
DEFAULT_MODEL = "llama-3.3-70b-versatile"
