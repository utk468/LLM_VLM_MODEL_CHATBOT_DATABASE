from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Chat(BaseModel):

    query: str = Field(..., description="The user's query.")
    answer: str = Field(..., description="The AI's response.")
    timestamp: datetime = Field(default_factory=datetime.now)

class Thread(BaseModel):

    thread_id: str = Field(..., description="Unique thread identifier.")
    chats: List[Chat] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.now)

class VisionAnalysis(BaseModel):

    thread_id: str = Field(..., description="The thread ID this analysis belongs to.")
    prompt: Optional[str] = Field(None, description="The user's text prompt.")
    description: str = Field(..., description="The VLM's analysis.")
    timestamp: datetime = Field(default_factory=datetime.now)

class User(BaseModel):

    username: str = Field(..., description="Unique username for the user.")
    password_hash: str = Field(..., description="Bcrypt hashed password.")
    created_at: datetime = Field(default_factory=datetime.now)
    threads: List[Thread] = Field(default_factory=list)
    vlm_records: List[VisionAnalysis] = Field(default_factory=list)

class UserRegister(BaseModel):

    username: str
    password: str

class UserLogin(BaseModel):

    username: str
    password: str
