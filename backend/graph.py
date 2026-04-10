from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from backend.state import ChatState
from backend.nodes import chat_node_direct, chat_node_tools, dynamic_tool_node
from backend.routing import route_query

# Define the graph
graph = StateGraph(ChatState)

# Add nodes
graph.add_node("chat_node_direct", chat_node_direct)
graph.add_node("chat_node_tools", chat_node_tools)
graph.add_node("tools", dynamic_tool_node)

# Add edges and conditional routing
graph.add_conditional_edges(START, route_query)

graph.add_conditional_edges(
    "chat_node_tools",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END
    }
)

graph.add_edge("tools", "chat_node_tools")

# Global chatbot instance (initialized during lifespan)
chatbot = None

async def init_chatbot(checkpointer):
    """
    Compiles the graph with the provided checkpointer and initializes the global chatbot.
    """
    global chatbot
    chatbot = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["tools"]
    )
    return chatbot
