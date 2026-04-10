from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

@tool
def web_search(query: str):
    """Search the web for live news, events, weather, and real-time data."""
    return DuckDuckGoSearchRun().run(query)
