from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool

@tool
def wikipedia(query: str):
    """Search Wikipedia for factual knowledge, history, people, and places."""
    wiki = WikipediaAPIWrapper()
    return WikipediaQueryRun(api_wrapper=wiki).run(query)
