import math
from langchain_core.tools import tool

@tool(description="Useful for evaluating mathematical expressions.")
def calculator(expression: str) -> str:

    try:

        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
