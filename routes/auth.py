from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import timedelta
import uuid

from schema.user import User, UserRegister, UserLogin
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user
from backend.config import MONGODB_URI, DATABASE_NAME, USERS_COLLECTION, ACCESS_TOKEN_EXPIRE_MINUTES

auth_router = APIRouter()

# Dependency to get DB collection
async def get_users_collection():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    return db[USERS_COLLECTION]

@auth_router.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister, collection = Depends(get_users_collection)):
    # Check if user already exists
    existing_user = await collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_id = str(uuid.uuid4())
    
    new_user = {
        "_id": user_id,
        "username": user.username,
        "password_hash": hashed_password,
    }
    
    await collection.insert_one(new_user)
    
    return {"message": "User registered successfully", "user_id": user_id}

@auth_router.post("/api/auth/login")
async def login_user(user: UserLogin, collection = Depends(get_users_collection)):
    # Retrieve user
    db_user = await collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    # Verify password
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user["_id"]), "username": db_user["username"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "username": db_user["username"]}

@auth_router.get("/api/auth/me")
async def read_users_me(user_id: str = Depends(get_current_user), collection = Depends(get_users_collection)):
    user = await collection.find_one({"_id": user_id})
    if user:
        return {"user_id": user["_id"], "username": user["username"]}
    raise HTTPException(status_code=404, detail="User not found")
