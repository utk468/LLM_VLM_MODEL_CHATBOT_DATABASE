from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from backend.config import MONGODB_URI, DATABASE_NAME, CHECKPOINTS_COLLECTION, USERS_COLLECTION

async def associate_thread_with_user(thread_id: str, user_id: str):
    """
    Associates a newly created thread with a specific user by adding it to their threads list.
    """
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        # Check if thread already associated to avoid duplicates
        existing = await db[USERS_COLLECTION].find_one(
            {"_id": user_id, "threads.thread_id": thread_id}
        )
        
        if not existing:
            await db[USERS_COLLECTION].update_one(
                {"_id": user_id},
                {"$push": {"threads": {
                    "thread_id": thread_id,
                    "chats": [],
                    "updated_at": datetime.now()
                }}}
            )
    except Exception as e:
        print(f"Error associating thread with user: {str(e)}")

async def add_chat_to_thread(user_id: str, thread_id: str, query: str, answer: str, image: str = None):
    """
    Adds a new chat turn (query and answer) to a specific thread in the user's document.
    Optionally stores an image (Base64) if provided.
    """
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        chat_entry = {
            "query": query,
            "answer": answer,
            "timestamp": datetime.now()
        }
        
        if image:
            chat_entry["image"] = image

        await db[USERS_COLLECTION].update_one(
            {"_id": user_id, "threads.thread_id": thread_id},
            {
                "$push": {
                    "threads.$.chats": chat_entry
                },
                "$set": {"threads.$.updated_at": datetime.now()}
            }
        )
    except Exception as e:
        print(f"Error adding chat to thread: {str(e)}")

async def get_all_threads(user_id: str = None, chatbot=None):
    """
    Returns all conversation thread IDs for a user.
    """
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        if user_id:
            user = await db[USERS_COLLECTION].find_one({"_id": user_id})
            if user and "threads" in user:
                # Sort by updated_at (descending)
                sorted_threads = sorted(user["threads"], key=lambda x: x.get("updated_at", 0), reverse=True)
                return [t["thread_id"] for t in sorted_threads]
            return []
        else:
            # Fallback (e.g. admin or dev mode)
            collection = db[CHECKPOINTS_COLLECTION]
            threads = await collection.distinct("thread_id")
            return threads
    except Exception as e:
        print(f"Error retrieving threads from MongoDB: {str(e)}")
        return []

async def delete_thread_from_db(thread_id: str, chatbot=None):
    """
    Deletes a thread from the MongoDB database (checkpoints and user document).
    """
    print(f"Deleting thread from MongoDB: {thread_id}")
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        # 1. Remove from all users' threads lists
        await db[USERS_COLLECTION].update_many(
            {},
            {"$pull": {"threads": {"thread_id": thread_id}}}
        )
        
        # 2. Delete from checkpoints and writes collections
        await db[CHECKPOINTS_COLLECTION].delete_many({"thread_id": thread_id})
        await db["checkpoint_writes"].delete_many({"thread_id": thread_id})
        
        # 3. Clean up VLM records associated with this thread (optional but good practice)
        await db[USERS_COLLECTION].update_many(
            {},
            {"$pull": {"vlm_records": {"thread_id": thread_id}}}
        )
        
        print(f"Thread {thread_id} deleted successfully from MongoDB.")
        return True
    except Exception as e:
        print(f"Error deleting thread {thread_id} from MongoDB: {str(e)}")
        return False
