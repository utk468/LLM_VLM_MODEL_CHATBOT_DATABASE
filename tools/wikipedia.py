from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool

@tool(description="Search Wikipedia for factual summaries, definitions, and encyclopedic knowledge.")
def wikipedia(query: str):

    try:
        wiki = WikipediaAPIWrapper()
        results = WikipediaQueryRun(api_wrapper=wiki).run(query)

        context_header = f"[SYSTEM CONTEXT: Factual information found on Wikipedia for '{query}'. Use this to answer the user accurately.]\n\n"

        if not results or "no results" in results.lower() or "cannot find" in results.lower():
            return f"Wikipedia could not find any relevant information for '{query}'."

        return context_header + results
    except Exception as e:
        return f"Wikipedia error: {str(e)}. Please try again."
