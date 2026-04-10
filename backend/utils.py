from copy import deepcopy
from langchain_core.messages import BaseMessage

def sanitize_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    Converts multimodal messages (containing image lists) into plain text
    so that text-only models don't crash.
    """
    new_messages = []
    for m in messages:
        # Create a copy so we don't modify the state's actual history
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
