from langchain_core.messages import HumanMessage
from backend.state import ChatState
from backend.llm import llm

def route_query(state: ChatState) -> str:
    """
    Determines whether to route to a tool-enabled node or a direct chat node.
    Uses keyword matching and LLM decision making for routing.
    """
    messages = state["messages"]
    if not messages:
        return "chat_node_direct"

    # If already in a tool loop
    if messages[-1].type == "tool":
        print("--- ROUTING: Continuing Tool Loop ---")
        return "chat_node_tools"

    query = str(messages[-1].content).lower()

    # Manual keyword routing for reliability
    urgent_tool_keywords = [
        "news", "today", "latest", "live", "weather", "calculator", "math", 
        "+", "-", "*", "/"
    ]

    if any(k in query for k in urgent_tool_keywords):
        print(f"--- ROUTING: Tool Path (Keyword Match: '{query}') ---")
        return "chat_node_tools"

    # LLM Decision for more complex cases
    prompt = f"""
    Decide if the user needs a TOOL or a DIRECT conversation.
    Available Tools: Search (News/Live), Wikipedia (Facts/History), Calculator (Math).

    User Input: "{query}"

    Respond only with 'TOOL' or 'DIRECT'.
    """
    
    try:
        decision = llm.invoke([HumanMessage(content=prompt)]).content.strip().upper()
        print(f"--- ROUTING DECISION: {decision} ---")
        return "chat_node_tools" if "TOOL" in decision else "chat_node_direct"
    except Exception as e:
        print(f"--- ROUTING ERROR: {e}. Defaulting to Direct. ---")
        return "chat_node_direct"
