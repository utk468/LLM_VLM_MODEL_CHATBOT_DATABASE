from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ChatState(TypedDict):
    """
    State definition for the LangGraph chatbot.
    Maintains a list of messages with the 'add_messages' annotator for history appending.
    """
    messages: Annotated[list[BaseMessage], add_messages]
