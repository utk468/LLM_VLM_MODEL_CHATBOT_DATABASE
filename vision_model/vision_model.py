import base64
import requests
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Load environment variables (GROQ_API_KEY)
load_dotenv()

class VisionModel:
    """
    PURPOSE:
    This class connects to Groq Cloud API using the 'llama-3.2-11b-vision-preview' model.
    It replaces the local Ollama/Moondream implementation.

    Input:
        - Image (Path, URL, or Base64)
        - Prompt
        - History (Optional)
    Output:
        - AI generated description/answer
    """

    def __init__(self):
        self.model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
        # Ensure API key is present
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "gsk_your_key_here":
            print("⚠️ WARNING: GROQ_API_KEY not found or default value used in .env")
        
        self.llm = ChatGroq(model=self.model_name, temperature=0)

    def _encode_image(self, image_path):
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except (IOError, Exception):
            return None

    def _fetch_image_from_url(self, image_url):
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")
        except requests.exceptions.RequestException:
            return None

    def query(self, prompt=None, image_path=None, image_url=None, history=None):
        """
        Main query function compatible with the application's existing flow.
        """
        if not image_path and not image_url and not history:
            return {"error": "Image or history required for Vision analysis."}

        base64_img = None
        if image_path:
            base64_img = self._encode_image(image_path)
        elif image_url:
            if image_url.startswith("http://") or image_url.startswith("https://"):
                base64_img = self._fetch_image_from_url(image_url)
            elif "base64," in image_url:
                base64_img = image_url.split("base64,")[1]
            else:
                base64_img = image_url

        if not base64_img and not history:
            return {"error": "Failed to extract image data."}

        # Prepare messages for Groq Vision
        messages = []
        
        # 1. System Message
        messages.append(SystemMessage(content="You are a helpful assistant that can see and describe images."))

        # 2. Add history if provided
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))

        # 3. Add current prompt with image
        user_content = []
        user_content.append({"type": "text", "text": prompt if prompt else "Describe this image in detail."})
        
        if base64_img:
            # Detect mime type or default to image/png
            # For simplicity using image/png as it works for base64 strings usually
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_img.strip()}"
                }
            })
            
        messages.append(HumanMessage(content=user_content))

        try:
            print(f" [Groq Vision] Analyzing with {self.model_name}...")
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return {"error": f"Groq API Failure: {str(e)}"}