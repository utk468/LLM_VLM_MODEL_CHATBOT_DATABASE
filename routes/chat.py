from subprocess import check_output
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import uuid
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from fastapi import APIRouter, Request, Depends
from backend.auth import get_current_user
import langgraph_backend
from langgraph_backend import get_all_threads, delete_thread_from_db, add_chat_to_thread, associate_thread_with_user
from vision_model.vision_model import VisionModel
from vision_model.vision_memory import vision_memory_db
from backend.config import USERS_COLLECTION, DATABASE_NAME, MONGODB_URI
from motor.motor_asyncio import AsyncIOMotorClient

chat_router = APIRouter()
vision_api = VisionModel()

@chat_router.post("/api/vision")
async def vision_chat(request: Request, user_id: str = Depends(get_current_user)):

    data = await request.json()
    prompt = data.get('message')                       
    image_data = data.get('image')                  
    thread_id = data.get('thread_id')                 

    history = []

    active_image = image_data 

    if thread_id and langgraph_backend.chatbot:

        try:
            config = {"configurable": {"thread_id": thread_id}}

            state = await langgraph_backend.chatbot.aget_state(config)

            prev_messages = state.values.get("messages", [])

            for msg in prev_messages:

                role = "user" if isinstance(msg, HumanMessage) else "assistant"

                content = msg.content

                if isinstance(content, list):

                    text_parts = [
                        item["text"] 
                        for item in content 
                        if item.get("type") == "text"
                    ]

                    content = " ".join(text_parts)

                    if not active_image:
                        image_parts = [
                            item["image_url"]["url"]
                            for item in content
                            if isinstance(item, dict) and item.get("type") == "image_url"
                        ]

                        if image_parts:
                            active_image = image_parts[0]

                history.append({
                    "role": role,
                    "content": content
                })

            if not active_image:
                for msg in reversed(prev_messages):

                    if isinstance(msg.content, list):
                        for item in msg.content:
                            if isinstance(item, dict) and item.get("type") == "image_url":
                                active_image = item["image_url"]["url"]
                                break

                    if active_image:
                        break

        except Exception as e:
            print(f"Error fetching history/image for vision: {str(e)}")

    if not active_image:
        return {
            "type": "error",
            "content": "No active image found. Please upload an image first."
        }

    result = vision_api.query(
        prompt,
        image_path=None,
        image_url=active_image,
        history=history
    )

    if isinstance(result, dict) and "error" in result:
        return {
            "type": "error",
            "content": result["error"]
        }

    response_text = result if isinstance(result, str) else str(result)

    if thread_id and langgraph_backend.chatbot:
        try:
            config = {"configurable": {"thread_id": thread_id}}

            messages = [
                HumanMessage(content=[
                    {"type": "text", "text": prompt},

                    {
                        "type": "image_url",
                        "image_url": {
                            "url": active_image if active_image.startswith("data:")
                            else f"data:image/png;base64,{active_image}"
                        }
                    }
                ]),

                AIMessage(content=response_text)
            ]

            await langgraph_backend.chatbot.aupdate_state(
                config,
                {"messages": messages},
                as_node="chat_node_direct"
            )

            print(f"Vision interaction persisted to thread: {thread_id}")

            await associate_thread_with_user(thread_id, user_id)

            print(f"--- SYNCING VISION TO DB: Image size {len(active_image) if active_image else 0} ---")
            await add_chat_to_thread(user_id, thread_id, prompt, response_text, image=active_image)

            saved = await vision_memory_db.save_analysis(
                thread_id,
                user_id,
                prompt,
                response_text
            )

            if saved:
                print(f"Saved to MongoDB (User Doc Thread: {thread_id})")

        except Exception as e:
            print(f"Persistence error: {str(e)}")

            import logging
            logging.error(
                f"Vision persistence failed for thread {thread_id}",
                exc_info=True
            )

    return {
        "type": "content",
        "content": response_text
    }

@chat_router.get("/api/threads")
async def list_threads(user_id: str = Depends(get_current_user)):

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    user = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if not user or "threads" not in user:
        return []

    sorted_threads = sorted(user["threads"], key=lambda x: x.get("updated_at", 0), reverse=True)

    threads = []
    for t in sorted_threads:
        t_id = t["thread_id"]
        chats = t.get("chats", [])

        title = "New Conversation"
        if chats:
            first_msg = chats[0]["query"]
            title = first_msg[:30] + "..." if len(first_msg) > 30 else first_msg

        threads.append({"id": t_id, "title": title})

    return threads

@chat_router.get("/api/history/{thread_id}")
async def get_history(thread_id: str, user_id: str = Depends(get_current_user)):

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    user = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if not user or "threads" not in user:
        return {"messages": []}

    thread = next((t for t in user["threads"] if t.get("thread_id") == thread_id), None)
    if not thread:
        return {"messages": []}

    formatted = []
    for chat in thread.get("chats", []):
        human_msg = {
            "role": "human",
            "content": chat["query"]
        }
        if chat.get("image"):
            human_msg["image"] = chat["image"]

        formatted.append(human_msg)

        formatted.append({
            "role": "assistant",
            "content": chat["answer"]
        })

    return {"messages": formatted}

@chat_router.post("/api/chat")
async def chat(request: Request, user_id: str = Depends(get_current_user)):

    data = await request.json()
    user_msg = data.get('message')

    thread_id = data.get('thread_id', str(uuid.uuid4()))

    config = {"configurable": {"thread_id": thread_id}}

    async def generate():

        latest_desc = ""
        if thread_id:

            await langgraph_backend.associate_thread_with_user(thread_id, user_id)
            try:

                latest_desc = await vision_memory_db.get_latest_description(thread_id, user_id)
            except Exception as e:
                print(f" Error fetching native vision context: {str(e)}")

        instruction = """You are a helpful, professional, and intelligent AI assistant.

OUTPUT FORMATTING MANDATE:
- Always format ALL metrics, statistics, currency rates, comparisons, weather forecasts, or tabular data as clean Markdown Pipe Tables (| Metric | Value |).
- Always use Markdown section headers (### Header) and bulleted lists (-) to organize content logically into a clean, structured output.
- Never output loose, unformatted space-aligned columns or plain text blocks for structured data."""
        if latest_desc:
            instruction += f"\n\n[USER JUST SHOWED YOU AN IMAGE]\nDescription from your Vision Memory: {latest_desc}\n\nUse this description if the user asks for more details, follow-up questions, or mentions what they just showed you."

        system_msg = SystemMessage(content=instruction)

        try:
            async for chunk, metadata in langgraph_backend.chatbot.astream(
                {"messages": [system_msg, HumanMessage(content=user_msg)]}, 
                config=config, 
                stream_mode="messages"
            ):

                if isinstance(chunk, AIMessage) and chunk.content:

                    print(chunk.content, end="", flush=True)

                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
        except Exception as e:
            print(f"--- STREAM ERROR: {str(e)} ---")
            yield f"data: {json.dumps({'type': 'content', 'content': f'Communication Error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            return

        else:

            final_state = await langgraph_backend.chatbot.aget_state(config)
            print(f"--- DEBUG: Graph State Next: {final_state.next} ---")

            if final_state.next and any("tools" in str(s) for s in final_state.next):

                tool_call = None
                for msg in reversed(final_state.values.get("messages", [])):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_call = msg.tool_calls[0]
                        break

                if tool_call:
                    print(f"\n--- HITL INTERRUPT: AI needs tool '{tool_call['name']}' ---")
                    yield f"data: {json.dumps({'type': 'hitl', 'action': tool_call['name'], 'args': tool_call.get('args', {})})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"

            else:

                print("\n--- STREAM COMPLETE ---")
                msgs = final_state.values.get("messages", [])
                if len(msgs) >= 2:
                    ai_response = ""
                    for m in reversed(msgs):
                        if isinstance(m, AIMessage) and m.content:
                            ai_response = m.content
                            break

                    if ai_response:

                        img_to_save = None
                        if isinstance(user_msg, list):
                            for part in user_msg:
                                if isinstance(part, dict) and part.get("type") == "image_url":
                                    img_to_save = part["image_url"]["url"]

                        await add_chat_to_thread(user_id, thread_id, str(user_msg), ai_response, image=img_to_save)
                        print(f"Chat turn synced to User doc (Thread: {thread_id})")

                yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@chat_router.post("/api/chat/resume")
async def resume(request: Request, user_id: str = Depends(get_current_user)):

    data = await request.json()

    decision = data.get('decision')

    thread_id = data.get('thread_id')

    config = {"configurable": {"thread_id": thread_id}}

    state = await langgraph_backend.chatbot.aget_state(config)

    if not state.values or "messages" not in state.values or not state.values["messages"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Thread state not found or invalid. Please refresh and try again."}
        )

    last_message = state.values["messages"][-1]

    async def generate():

        if decision == 'allow':
            stream = langgraph_backend.chatbot.astream(None, config=config, stream_mode="messages")

        else:
            tool_messages = []
            for tc in last_message.tool_calls:
                tool_messages.append(ToolMessage(
                    tool_call_id=tc["id"],
                    name=tc["name"],
                    content="User denied tool execution."
                ))
            stream = langgraph_backend.chatbot.astream({"messages": tool_messages}, config=config, stream_mode="messages")

        async for chunk, metadata in stream:

            if isinstance(chunk, AIMessage) and chunk.content:

                yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"

        new_state = await langgraph_backend.chatbot.aget_state(config)

        msgs = new_state.values.get("messages", [])
        if len(msgs) >= 2:
            user_msg = ""
            ai_msg = ""
            for m in reversed(msgs):
                if isinstance(m, AIMessage) and not ai_msg:
                    ai_msg = m.content
                elif isinstance(m, HumanMessage) and not user_msg:
                    user_msg = m.content
                if ai_msg and user_msg: break

            if user_msg and ai_msg:

                img_to_save = None
                for m in reversed(msgs):
                    if isinstance(m, HumanMessage) and isinstance(m.content, list):
                        for part in m.content:
                            if isinstance(part, dict) and part.get("type") == "image_url":
                                img_to_save = part["image_url"]["url"]
                                break
                    if img_to_save: break

                await add_chat_to_thread(user_id, thread_id, user_msg, ai_msg, image=img_to_save)

        if new_state.next and "tools" in new_state.next:
            tool_call = None
            for msg in reversed(new_state.values.get("messages", [])):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_call = msg.tool_calls[0]
                    break
            if tool_call:
                yield f"data: {json.dumps({'type': 'hitl', 'action': tool_call['name'], 'args': tool_call.get('args', {})})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@chat_router.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str, user_id: str = Depends(get_current_user)):
    await langgraph_backend.delete_thread_from_db(thread_id)
    return {"success": True}
