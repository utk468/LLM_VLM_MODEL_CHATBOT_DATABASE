import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.index import index_router
from routes.chat import chat_router
from routes.mcp import mcp_router
from routes.tools import tools_router
from routes.auth import auth_router
from langgraph_backend import init_chatbot
from tools.mcp_tools import mcp_manager
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from backend.config import MONGODB_URI, DATABASE_NAME



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing LangGraph Chatbot with MongoDBSaver...")
    
    # Initialize MongoDB client
    client = MongoClient(MONGODB_URI)
    checkpointer = MongoDBSaver(client, db_name=DATABASE_NAME)
    
    await init_chatbot(checkpointer)
    print("Chatbot initialized successfully.")
        
    yield
    
    print("Shutting down...")
    await mcp_manager.disconnect()
    client.close()

def create_app():
    app = FastAPI(
        title="Fast Chatbot with RAG & MCP",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(index_router)
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(mcp_router)
    app.include_router(tools_router)
    
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    return app

app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=5000)