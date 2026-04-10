import math
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Answer mathematical questions by evaluating expressions like '2+2'."""
    try:
        # Restricted eval for basic safety
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
