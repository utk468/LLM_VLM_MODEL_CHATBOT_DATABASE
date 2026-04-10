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






# Vision Inference Endpoint
@chat_router.post("/api/vision")
async def vision_chat(request: Request, user_id: str = Depends(get_current_user)):
 

    # Extract request data
    data = await request.json()
    prompt = data.get('message')      # User text input
    image_data = data.get('image')    # Base64 image
    thread_id = data.get('thread_id')# Conversation ID

    # Fetch history
    history = []

    # Active image = current request image
    active_image = image_data 

    # If thread exists → load past messages
    if thread_id and langgraph_backend.chatbot:

        try:
            config = {"configurable": {"thread_id": thread_id}}

            # Get previous state (conversation history)
            state = await langgraph_backend.chatbot.aget_state(config)

            # Extract stored messages
            prev_messages = state.values.get("messages", [])

            # Loop through history
            for msg in prev_messages:

                # Identify role
                role = "user" if isinstance(msg, HumanMessage) else "assistant"

                content = msg.content

                #  If multimodal (text + image)
                if isinstance(content, list):

                    # Extract only text parts
                    text_parts = [
                        item["text"] 
                        for item in content 
                        if item.get("type") == "text"
                    ]

                    content = " ".join(text_parts)

                    # If no image in current request → try history
                    if not active_image:
                        image_parts = [
                            item["image_url"]["url"]
                            for item in content
                            if isinstance(item, dict) and item.get("type") == "image_url"
                        ]

                        if image_parts:
                            active_image = image_parts[0]

                # Add to history (text only)
                history.append({
                    "role": role,
                    "content": content
                })

            # Fallback: search image backwards
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

    # No image anywhere → stop
    if not active_image:
        return {
            "type": "error",
            "content": "No active image found. Please upload an image first."
        }

    # calling the vision model
    result = vision_api.query(
        prompt,
        image_path=None,
        image_url=active_image,
        history=history
    )

    # Model error
    if isinstance(result, dict) and "error" in result:
        return {
            "type": "error",
            "content": result["error"]
        }

    # Ensure response is string
    response_text = result if isinstance(result, str) else str(result)

    # SAVE TO MEMORY
    if thread_id and langgraph_backend.chatbot:
        try:
            config = {"configurable": {"thread_id": thread_id}}

            # Format messages for LangGraph
            messages = [
                HumanMessage(content=[
                    {"type": "text", "text": prompt},

                    # Save image in base64 format
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

            # Save to LangGraph (short-term memory)
            await langgraph_backend.chatbot.aupdate_state(
                config,
                {"messages": messages},
                as_node="chat_node_direct"
            )

            print(f"Vision interaction persisted to thread: {thread_id}")

            # Associate thread with user (adds to user document's 'threads' list if not present)
            await associate_thread_with_user(thread_id, user_id)

            # SAVE TO MONGODB (LONG MEMORY - HIERARCHICAL SYNC)
            await add_chat_to_thread(user_id, thread_id, prompt, response_text, image=active_image)

            # Also save to VLM Records list in User document
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

    # respone
    return {
        "type": "content",
        "content": response_text
    }






#fetches all threads using langgraph_backend
#api endpoint
#here we are using async and await because langgraph_backend is async
@chat_router.get("/api/threads")
async def list_threads(user_id: str = Depends(get_current_user)):
    """
    Fetches all thread summaries for the logged-in user from their User document.
    """
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    user = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if not user or "threads" not in user:
        return []

    # Sort threads by updated_at (descending)
    sorted_threads = sorted(user["threads"], key=lambda x: x.get("updated_at", 0), reverse=True)
    
    threads = []
    for t in sorted_threads:
        t_id = t["thread_id"]
        chats = t.get("chats", [])
        
        # Determine title (first user message)
        title = "New Conversation"
        if chats:
            first_msg = chats[0]["query"]
            title = first_msg[:30] + "..." if len(first_msg) > 30 else first_msg
        
        threads.append({"id": t_id, "title": title})
    
    return threads




  


#here we are getting the history of the chat
@chat_router.get("/api/history/{thread_id}")
async def get_history(thread_id: str, user_id: str = Depends(get_current_user)):
    """
    Retrieves full chat history for a specific thread from the User document.
    """
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    user = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if not user or "threads" not in user:
        return {"messages": []}

    # Find the requested thread
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





#here we are getting the chat response 
#HITL loop 
#post request to get the user input message from the frontend and passes the message to the backend 
@chat_router.post("/api/chat")
async def chat(request: Request, user_id: str = Depends(get_current_user)):
    #getting the user input message from the frontend
    data = await request.json()
    user_msg = data.get('message')
    #getting the thread id from the frontend 
    thread_id = data.get('thread_id', str(uuid.uuid4()))
    #setting the config for the thread
    config = {"configurable": {"thread_id": thread_id}}
    

    # generator function where we are generating message in stream
    async def generate():
        # --- NATIVE VISION CONTEXT: Auto-fetch and inject LATEST image analysis ---
        latest_desc = ""
        if thread_id:
            # Associate this thread with the user securely
            await langgraph_backend.associate_thread_with_user(thread_id, user_id)
            try:
                # Fetch only the single most recent vision result for this thread
                latest_desc = await vision_memory_db.get_latest_description(thread_id, user_id)
            except Exception as e:
                print(f" Error fetching native vision context: {str(e)}")
        
        # Build dynamic system instruction
        instruction = "You are a helpful and intelligent AI assistant."
        if latest_desc:
            instruction += f"\n\n[USER JUST SHOWED YOU AN IMAGE]\nDescription from your Vision Memory: {latest_desc}\n\nUse this description if the user asks for more details, follow-up questions, or mentions what they just showed you."
            
        system_msg = SystemMessage(content=instruction)
        
        try:
            async for chunk, metadata in langgraph_backend.chatbot.astream(
                {"messages": [system_msg, HumanMessage(content=user_msg)]}, 
                config=config, 
                stream_mode="messages"
            ):
                # only ai message is chunked
                if isinstance(chunk, AIMessage) and chunk.content:
                    # Echo to terminal
                    print(chunk.content, end="", flush=True)
                    # yield send chunk to frontend
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
        except Exception as e:
            print(f"--- STREAM ERROR: {str(e)} ---")
            yield f"data: {json.dumps({'type': 'content', 'content': f'Communication Error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            return
        
        #checking if ai want to use the tool if yes then sending hitl message to the frontend
        #if no tool calling sending end message to the frontend
        # Final turn completion or Tool Interrupt
        else:
            # Check for HITL/Tool Interrupt
            final_state = await langgraph_backend.chatbot.aget_state(config)
            print(f"--- DEBUG: Graph State Next: {final_state.next} ---")
            
            if final_state.next and any("tools" in str(s) for s in final_state.next):
                # AI wants to call a tool - send HITL prompt to frontend
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
                # SYNC TO HIERARCHICAL SCHEMA
                print("\n--- STREAM COMPLETE ---")
                msgs = final_state.values.get("messages", [])
                if len(msgs) >= 2:
                    ai_response = ""
                    for m in reversed(msgs):
                        if isinstance(m, AIMessage) and m.content:
                            ai_response = m.content
                            break
                    
                    if ai_response:
                        # Check for image in user message (multimodal support for standard chat)
                        img_to_save = None
                        if isinstance(user_msg, list):
                            for part in user_msg:
                                if isinstance(part, dict) and part.get("type") == "image_url":
                                    img_to_save = part["image_url"]["url"]
                        
                        await add_chat_to_thread(user_id, thread_id, str(user_msg), ai_response, image=img_to_save)
                        print(f"Chat turn synced to User doc (Thread: {thread_id})")

                yield f"data: {json.dumps({'type': 'end'})}\n\n"


    # generate() creates the stream
    # StreamingResponse sends that stream to the client
    # media_type="text/event-stream" is the format for server-sent events
    return StreamingResponse(generate(), media_type="text/event-stream")





#this endpoint is called after frontend receives a hitl event
#where we are resuming chat when we allow the hitl loop
#example data: {"decision": "allow", "thread_id": "abc123"} getting from frontend 
@chat_router.post("/api/chat/resume")
async def resume(request: Request, user_id: str = Depends(get_current_user)):
    
    data = await request.json()
    #getting the decision from the frontend
    decision = data.get('decision')
    #getting the thread id from the frontend 
    thread_id = data.get('thread_id')
    #setting the config for the thread
    config = {"configurable": {"thread_id": thread_id}}
    
    # getting the current state of the thread here we have messages and other data
    state = await langgraph_backend.chatbot.aget_state(config)
    
    # Validation: Ensure state and messages exist to prevent crash
    if not state.values or "messages" not in state.values or not state.values["messages"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Thread state not found or invalid. Please refresh and try again."}
        )
        
    # taking last message from the thread history using value function 
    # because it contains tool call information as here we are resuming the chat
    last_message = state.values["messages"][-1]
    

    # generator function where we are generating message in stream
    async def generate():
        # if decision is allow then we are resuming the chat
        if decision == 'allow':
            stream = langgraph_backend.chatbot.astream(None, config=config, stream_mode="messages")
            # astream() function where it is streaming output from LLM
            #chatbot.astream() takes the user input message and the config as arguments
            #here user input is None because we are resuming the chat
            #it returns a stream of chunks
            #each chunk is a dictionary that contains the type of the chunk and the content of the chunk
        
        # if decision is deny then we are sending tool messages to the frontend
        # here we are sending tool messages to the frontend
        # that no tool is called now ai will respond that it cannot perform the action
        else:
            tool_messages = []
            for tc in last_message.tool_calls:
                tool_messages.append(ToolMessage(
                    tool_call_id=tc["id"],
                    name=tc["name"],
                    content="User denied tool execution."
                ))
            stream = langgraph_backend.chatbot.astream({"messages": tool_messages}, config=config, stream_mode="messages")


        # generator function where we are generating message in stream
        async for chunk, metadata in stream:
            #checking if the chunk is AIMessage and has content
            if isinstance(chunk, AIMessage) and chunk.content:
                #yield send chunk to frontend
                yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
        

        # After streaming → sync and return
        new_state = await langgraph_backend.chatbot.aget_state(config)
        
        # Extract user message and final AI message
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
                # Extract image if present in history
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
            

    # StreamingResponse sends that stream to the client
    # media_type="text/event-stream" is the format for server-sent events
    return StreamingResponse(generate(), media_type="text/event-stream")



#deleting the thread from the database
#which will delete the chat history
#here we are calling delete_thread_from_db function
#which is defined in the langgraph_backend.py file  
@chat_router.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str, user_id: str = Depends(get_current_user)):
    await langgraph_backend.delete_thread_from_db(thread_id)
    return {"success": True}
