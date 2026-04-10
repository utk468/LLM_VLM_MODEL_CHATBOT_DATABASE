from fastapi import APIRouter
from fastapi.responses import FileResponse
import os


index_router = APIRouter()


#we are using fileresponse from fastapi to serve the index.html file
#get request to get the index.html file
@index_router.get("/")
async def index():
    return FileResponse(os.path.join("templates", "index.html"))

@index_router.get("/login")
async def login():
    return FileResponse(os.path.join("templates", "login.html"))

@index_router.get("/register")
async def register():
    return FileResponse(os.path.join("templates", "register.html"))
