from langchain_groq import ChatGroq
from backend.config import DEFAULT_MODEL
from tools import (
    calculator,
    web_search,
    wikipedia,
    query_uploaded_document
)
from tools.mcp_tools import mcp_manager

# Initialize LLM
llm = ChatGroq(
    model=DEFAULT_MODEL,
    temperature=0.1
)

# Static tools list
static_tools = [
    calculator,
    web_search,
    wikipedia,
    query_uploaded_document
]

def get_llm_with_tools():
    """
    Dynamically binds tools (static + MCP) to the LLM.
    Ensures all tools have descriptions before binding.
    """
    all_tools = []
    # Combine static tools and current MCP tools
    for t in (static_tools or []) + (mcp_manager.tools or []):
        if hasattr(t, "description") and t.description:
            all_tools.append(t)
        else:
            print(f"⚠️ Skipping tool {getattr(t, 'name', 'unknown')} due to missing description.")
    
    return llm.bind_tools(all_tools, tool_choice="auto")
