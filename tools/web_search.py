from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.tools import tool
from datetime import datetime

@tool
def web_search(query: str):
    """Search the web for live news, events, weather, and real-time data."""
    try:
        # 1. Add current date to the query to force latest results
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Adding 'latest' or the date helps DuckDuckGo prioritize recent info
        enhanced_query = f"{query} latest {current_date}"
        
        search = DuckDuckGoSearchAPIWrapper(max_results=5)
        results = search.run(enhanced_query)
        
        # 2. Add a 'System Context' to the output so the AI knows this is LIVE data
        context_header = f"[SYSTEM CONTEXT: Information found on {current_date}. Use this data to answer the user accurately.]\n\n"
        
        if not results or "no results" in results.lower():
            return f"No recent results found for '{query}' on {current_date}. Try a different query."
            
        return context_header + results
        
    except Exception as e:
        return f"Search error: {str(e)}. Please try again."
