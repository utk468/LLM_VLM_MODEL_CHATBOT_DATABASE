from dotenv import load_dotenv
import os

def load_config():
    load_dotenv()

load_config()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_db")

USERS_COLLECTION = "users"
CHECKPOINTS_COLLECTION = "checkpoints"

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-dev-only")                             
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7         

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-oss-120b")
