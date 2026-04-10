from copy import deepcopy
from langchain_core.messages import BaseMessage

def sanitize_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    Converts multimodal messages (containing image lists) into plain text.
    Strictly preserves ToolMessage and AIMessage metadata for Groq compatibility.
    """
    new_messages = []
    for m in messages:
        # If it's a ToolMessage or an AIMessage with tool calls, pass it through exactly as is
        # to ensure tool_call_id and tool_calls metadata are preserved.
        if m.type == "tool" or (m.type == "ai" and getattr(m, "tool_calls", None)):
            new_messages.append(m)
            continue

        m_copy = deepcopy(m)
        if isinstance(m_copy.content, list):
            text_parts = []
            for item in m_copy.content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        text_parts.append("[Image attached]")
                else:
                    text_parts.append(str(item))
            m_copy.content = "\n".join(text_parts)
        
        new_messages.append(m_copy)
    return new_messages
