
from backend.config import load_config
from backend.state import ChatState
from backend.utils import sanitize_messages
from backend.llm import llm, get_llm_with_tools, static_tools as tools
from backend.routing import route_query
from backend.nodes import chat_node_direct, chat_node_tools, dynamic_tool_node
from backend.graph import init_chatbot, graph

import backend.graph as graph_mod

from tools import (
    calculator,
    web_search,
    wikipedia
)

from backend import database

async def get_all_threads(user_id: str = None):

    return await database.get_all_threads(user_id, graph_mod.chatbot)

async def delete_thread_from_db(thread_id: str):

    return await database.delete_thread_from_db(thread_id, graph_mod.chatbot)

async def associate_thread_with_user(thread_id: str, user_id: str):
    return await database.associate_thread_with_user(thread_id, user_id)

async def add_chat_to_thread(user_id: str, thread_id: str, query: str, answer: str, image: str = None):
    return await database.add_chat_to_thread(user_id, thread_id, query, answer, image=image)

def __getattr__(name):
    if name == "chatbot":
        return graph_mod.chatbot
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

