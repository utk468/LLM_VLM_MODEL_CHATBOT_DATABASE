import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import MONGODB_URI, DATABASE_NAME, USERS_COLLECTION
from schema.user import VisionAnalysis

class VisionMemory:
    """
    PURPOSE:
    This class manages vision-based chatbot responses stored hierarchically 
    within the User document in MongoDB.
    """

    def __init__(self, uri=None, db_name=None):
        self.uri = uri or MONGODB_URI
        self.db_name = db_name or DATABASE_NAME
        self.client = None
        self.db = None
        self.users_collection = None

    def _ensure_connected(self):
        if self.client is None:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            self.users_collection = self.db[USERS_COLLECTION]

    async def save_analysis(self, thread_id: str, user_id: str, prompt: str, description: str):
        """
        Save a new vision analysis record into the User's document.
        """
        self._ensure_connected()
        
        analysis = VisionAnalysis(
            thread_id=thread_id,
            prompt=prompt,
            description=description,
            timestamp=datetime.now()
        )
        
        try:
            await self.users_collection.update_one(
                {"_id": user_id},
                {"$push": {"vlm_records": analysis.model_dump()}}
            )
            return True
        except Exception as e:
            print(f"Error saving to VisionMemory (User doc): {str(e)}")
            return False

    async def get_thread_context(self, thread_id: str, user_id: str):
        """
        Retrieve all past vision records for a specific thread from the User document.
        """
        self._ensure_connected()
        
        try:
            user = await self.users_collection.find_one({"_id": user_id})
            if not user or "vlm_records" not in user:
                return "No past vision analysis found."

            # Filter records for this thread
            thread_records = [r for r in user["vlm_records"] if r.get("thread_id") == thread_id]
            
            if not thread_records:
                return "No past vision analysis found for this thread."

            thread_records.sort(key=lambda x: x.get("timestamp", datetime.min))

            context = "PAST VISION ANALYSIS RECORDS\n"
            for i, row in enumerate(thread_records, 1):
                item = VisionAnalysis(**row)
                ts_str = item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                context += f"Record {i} ({ts_str}):\n"
                context += f"User asked: {item.prompt}\n"
                context += f"Vision Result: {item.description}\n\n"

            return context
        except Exception as e:
            return f"Error retrieving Vision context data: {str(e)}"

    async def get_latest_description(self, thread_id: str, user_id: str):
        """
        Get the latest vision response for this thread from the User document.
        """
        self._ensure_connected()
        
        try:
            user = await self.users_collection.find_one({"_id": user_id})
            if not user or "vlm_records" not in user:
                return None

            thread_records = [r for r in user["vlm_records"] if r.get("thread_id") == thread_id]
            if not thread_records:
                return None

            # Get latest by timestamp
            latest = max(thread_records, key=lambda x: x.get("timestamp", datetime.min))
            return latest.get("description")
        except Exception as e:
            print(f"Error fetching latest vision desc: {str(e)}")
            return None

    async def show_all_records(self, user_id: str):
        """
        Debug function to print all records for a user.
        """
        self._ensure_connected()
        try:
            user = await self.users_collection.find_one({"_id": user_id})
            if not user or "vlm_records" not in user:
                print("\nNO VISION RECORDS FOUND FOR USER.")
                return

            print(f"\n ALL VISION MEMORY RECORDS FOR {user_id}:")
            for i, row in enumerate(user["vlm_records"], 1):
                item = VisionAnalysis(**row)
                print(f"🔹 [RECORD {i}]")
                print(f"   Thread ID   : {item.thread_id}")
                print(f"   User Prompt : {item.prompt}")
                print(f"   VLM Answer  : {item.description[:100]}..." if len(item.description) > 100 else f"   VLM Answer  : {item.description}")
                print(f"   Timestamp   : {item.timestamp}")
                print("-" * 50)
        except Exception as e:
            print(f"Error showing records: {str(e)}")

# Global instance
vision_memory_db = VisionMemory()
