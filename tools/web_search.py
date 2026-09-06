from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.tools import tool
from datetime import datetime

@tool(description="Search the web for current events, real-time news, and general web queries.")
def web_search(query: str):

    try:

        current_date = datetime.now().strftime("%Y-%m-%d")

        enhanced_query = f"{query} latest {current_date}"

        search = DuckDuckGoSearchAPIWrapper(max_results=5)
        results = search.run(enhanced_query)

        context_header = f"[SYSTEM CONTEXT: Information found on {current_date}. Use this data to answer the user accurately.]\n\n"

        if not results or "no results" in results.lower():
            return f"No recent results found for '{query}' on {current_date}. Try a different query."

        return context_header + results

    except Exception as e:
        return f"Search error: {str(e)}. Please try again."
