import traceback
import json
import re
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from backend.state import ChatState
from backend.utils import sanitize_messages
from backend.llm import llm, get_llm_with_tools, static_tools
from tools.mcp_tools import mcp_manager

def chat_node_direct(state: ChatState):
    """
    Handles normal conversation without tools.
    """
    messages = state["messages"]
    system_prompt = SystemMessage(content="""
    You are a friendly assistant.
    Answer naturally and conversationally.
    """)

    # Sanitize history for text-only model
    processed_messages = sanitize_messages([system_prompt] + messages)
    response = llm.invoke(processed_messages)

    return {"messages": [response]}

def chat_node_tools(state: ChatState):
    """
    Handles tool-based reasoning using the primary system prompt.
    """
    messages = state["messages"]

    # REASONING PROMPT: Used when the model needs to decide which tool to use.
    reasoning_instruction = SystemMessage(content="""
You are an advanced AI assistant. Your goal is to help the user by using tools when necessary.
Guidelines:
1. For real-time data, facts, news, or weather, you MUST use the appropriate tool.
2. Output a native tool call. DO NOT wrap it in text or conversational fillers.
3. If you have enough information, answer the user directly.
""")

    # SUMMARIZATION PROMPT: Used after a tool has returned data.
    summarization_instruction = SystemMessage(content="""
You are a helpful assistant. You have just received information from a tool.
Your task is to summarize this information naturally for the user.
DO NOT call any more tools. Just explain the results you were given.
""")

    if messages and messages[-1].type == "tool":
        model_to_use = llm
        current_instruction = summarization_instruction
        print("--- MODE: Summarizing Tool Result ---")
    else:
        model_to_use = get_llm_with_tools()
        current_instruction = reasoning_instruction
        print("--- MODE: Reasoning/Tool Selection ---")

    try:
        # CONSOLIDATE SYSTEM MESSAGES
        system_content = current_instruction.content
        conv_messages = []
        
        for m in messages:
            if isinstance(m, SystemMessage):
                system_content += "\n\n" + str(m.content)
            else:
                conv_messages.append(m)
        
        merged_system = SystemMessage(content=system_content)
        final_history = [merged_system] + conv_messages

        # Sanitize history for text-only model
        processed_messages = sanitize_messages(final_history)
        response = model_to_use.invoke(processed_messages)
        
        # LOGGING FOR DEBUGGING
        if hasattr(response, "tool_calls") and response.tool_calls:
            print(f"--- LLM GENERATED NATIVE TOOL CALLS: {len(response.tool_calls)} ---")
        else:
            # FALLBACK: Check if model "hallucinated" a JSON tool call into its text response
            text_content = str(response.content)
            json_match = re.search(r'\{.*"name":\s*"([^"]+)".*\}', text_content, re.DOTALL)
            
            if json_match:
                print("--- DETECTED TEXT-BASED TOOL CALL (FALLBACK TRIGGERED) ---")
                try:
                    # Try to extract and clean the JSON
                    potential_json = json_match.group(0)
                    tool_data = json.loads(potential_json)
                    
                    # Manually inject into tool_calls format
                    response.tool_calls = [{
                        "name": tool_data.get("name"),
                        "args": tool_data.get("parameters") or tool_data.get("args") or {},
                        "id": f"call_{int(__import__('time').time())}"
                    }]
                    # Clear the content so it doesn't show in UI
                    response.content = text_content.replace(potential_json, "").strip()
                except Exception as parse_err:
                    print(f"--- FALLBACK PARSE FAILED: {parse_err} ---")
            
            if not getattr(response, "tool_calls", None):
                print(f"--- LLM GENERATED DIRECT RESPONSE ---")
                print(f"    Content snippet: {str(response.content)[:50]}...")
    except Exception as e:
        print(f"--- LLM ERROR (chat_node_tools): {str(e)} ---")
        
        # SMART RETRY: If it failed, try one more time with stricter instructions
        if "validation" in str(e).lower() or "malformed" in str(e).lower() or "tool" in str(e).lower():
            print("--- RETRYING TOOL CALL WITH REINFORCED JSON INSTRUCTION ---")
            retry_instruction = SystemMessage(content="""
            YOUR PREVIOUS ATTEMPT FAILED. 
            You must output a valid JSON tool call. 
            DO NOT add any text, XML tags, or conversational fillers. 
            JSON ONLY.
            """)
            try:
                retry_messages = sanitize_messages([retry_instruction] + messages)
                response = model_to_use.invoke(retry_messages)
                return {"messages": [response]}
            except Exception as retry_e:
                print(f"--- RETRY FAILED: {str(retry_e)} ---")
                e = retry_e # Fall through to normal error handling
        
        traceback.print_exc()
        return {
            "messages": [AIMessage(content=f"I encountered a technical error: {str(e)}. Please try again.")]
        }

    # POST-PROCESS: If the model echoed the tool-calling JSON into the content field, clear it.
    if hasattr(response, "tool_calls") and response.tool_calls:
        content_str = str(response.content).strip()
        if content_str.startswith("{") and content_str.endswith("}"):
            response.content = ""

    return {"messages": [response]}

async def dynamic_tool_node(state: ChatState):
    """
    Executes tool calls generated by the LLM.
    Handles both static tools and MCP tools dynamically.
    """
    all_tools = {t.name: t for t in (static_tools or []) + (mcp_manager.tools or [])}
    last_message = state["messages"][-1]

    outputs = []

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            name = tool_call["name"] if isinstance(tool_call, dict) else tool_call.name
            args = tool_call["args"] if isinstance(tool_call, dict) else tool_call.args
            tool_id = tool_call["id"] if isinstance(tool_call, dict) else tool_call.id

            # Robust argument handling
            if isinstance(args, str):
                args = {"query": args}
            if not isinstance(args, dict):
                args = {}

            print("\n" + "="*50)
            print(f"TOOL: {name}")
            print(f"ARGS: {args}")

            tool_obj = all_tools.get(name)

            if tool_obj:
                try:
                    if hasattr(tool_obj, "ainvoke"):
                        res = await tool_obj.ainvoke(args)
                    else:
                        res = tool_obj.invoke(args)
                except Exception as e:
                    print(f"Tool Error: {str(e)}")
                    res = f"Error executing tool {name}: {str(e)}"

                if res is None:
                    res = "Operation completed successfully"

                print(f"RESULT: {str(res)[:200]}...") 
                content = str(res)
            else:
                content = f"Tool {name} not found"

            print("="*50 + "\n")

            outputs.append(
                ToolMessage(
                    content=content,
                    tool_call_id=tool_id,
                    name=name,
                )
            )

    return {"messages": outputs} if outputs else state
