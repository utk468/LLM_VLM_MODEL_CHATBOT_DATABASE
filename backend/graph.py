from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from backend.state import ChatState
from backend.nodes import chat_node_direct, chat_node_tools, dynamic_tool_node
from backend.routing import route_query

graph = StateGraph(ChatState)

graph.add_node("chat_node_direct", chat_node_direct)
graph.add_node("chat_node_tools", chat_node_tools)
graph.add_node("tools", dynamic_tool_node)

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

chatbot = None

async def init_chatbot(checkpointer):

    global chatbot
    chatbot = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["tools"]
    )
    return chatbot
