"""
LangGraph Backend Facade
This file re-exports functions and variables from the modularized backend 
to maintain backward compatibility with existing routes and mainapp.
"""

# Re-exporting from modular components
from backend.config import load_config
from backend.state import ChatState
from backend.utils import sanitize_messages
from backend.llm import llm, get_llm_with_tools, static_tools as tools
from backend.routing import route_query
from backend.nodes import chat_node_direct, chat_node_tools, dynamic_tool_node
from backend.graph import init_chatbot, graph

# Accessing the live chatbot instance
import backend.graph as graph_mod

# Tools re-export for routes/tools.py
from tools import (
    calculator,
    web_search,
    wikipedia
)

# Database/Thread management wrappers for compatibility
from backend import database

async def get_all_threads(user_id: str = None):
    """Wrapper to maintain original signature"""
    return await database.get_all_threads(user_id, graph_mod.chatbot)

async def delete_thread_from_db(thread_id: str):
    """Wrapper to maintain original signature"""
    return await database.delete_thread_from_db(thread_id, graph_mod.chatbot)

async def associate_thread_with_user(thread_id: str, user_id: str):
    return await database.associate_thread_with_user(thread_id, user_id)

async def add_chat_to_thread(user_id: str, thread_id: str, query: str, answer: str):
    return await database.add_chat_to_thread(user_id, thread_id, query, answer)

# Property-like access for chatbot
def __getattr__(name):
    if name == "chatbot":
        return graph_mod.chatbot
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Compatibility with direct import 'from langgraph_backend import chatbot'
# Note: Since chatbot starts as None, we need to be careful.
# Most routes access it via 'langgraph_backend.chatbot' which __getattr__ handles.