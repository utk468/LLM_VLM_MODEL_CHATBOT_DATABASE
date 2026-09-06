from backend.state import ChatState

def route_query(state: ChatState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return "chat_node_direct"

    last_msg = messages[-1]
    if getattr(last_msg, "type", None) == "tool":
        print("--- ROUTING: Continuing Tool Loop ---")
        return "chat_node_tools"

    return "chat_node_tools"
