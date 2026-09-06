import base64
import io
import os
import requests
from dotenv import load_dotenv
from PIL import Image
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

class VisionModel:

    def __init__(self):
        self.model_name = "qwen/qwen3.8-27b"

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "gsk_your_key_here":
            print("⚠️ WARNING: GROQ_API_KEY not found or default value used in .env")

        self.llm = ChatGroq(model=self.model_name, temperature=0)

    def _compress_image(self, base64_str, max_dim=1024):
        try:
            image_data = base64.b64decode(base64_str.strip())
            img = Image.open(io.BytesIO(image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((max_dim, max_dim))
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            return base64.b64encode(output.getvalue()).decode("utf-8")
        except Exception:
            return base64_str

    def _encode_image(self, image_path):
        try:
            with open(image_path, "rb") as f:
                raw_b64 = base64.b64encode(f.read()).decode("utf-8")
                return self._compress_image(raw_b64)
        except (IOError, Exception):
            return None

    def _fetch_image_from_url(self, image_url):
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            raw_b64 = base64.b64encode(response.content).decode("utf-8")
            return self._compress_image(raw_b64)
        except requests.exceptions.RequestException:
            return None

    def query(self, prompt=None, image_path=None, image_url=None, history=None):

        if not image_path and not image_url and not history:
            return {"error": "Image or history required for Vision analysis."}

        base64_img = None
        if image_path:
            base64_img = self._encode_image(image_path)
        elif image_url:
            if image_url.startswith("http://") or image_url.startswith("https://"):
                base64_img = self._fetch_image_from_url(image_url)
            elif "base64," in image_url:
                raw_b64 = image_url.split("base64,")[1]
                base64_img = self._compress_image(raw_b64)
            else:
                base64_img = self._compress_image(image_url)

        if not base64_img and not history:
            return {"error": "Failed to extract image data."}

        messages = []

        messages.append(SystemMessage(content="""You are a helpful assistant that can see, describe, and analyze images.
Always format any observations, metrics, objects, or comparisons using Markdown Pipe Tables (| Item | Details |), ### section headers, and bulleted lists (-) for a clean, structured output."""))

        if history:
            recent_history = history[-6:]
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
                    content_str = " ".join(text_parts) if text_parts else str(content)
                else:
                    content_str = str(content)
                    
                if role == "user":
                    messages.append(HumanMessage(content=content_str))
                else:
                    messages.append(AIMessage(content=content_str))

        user_content = []
        user_content.append({"type": "text", "text": prompt if prompt else "Describe this image in detail."})

        if base64_img:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img.strip()}"
                }
            })

        messages.append(HumanMessage(content=user_content))

        try:
            print(f" [Groq Vision] Analyzing with {self.model_name}...")
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return {"error": f"Groq API Failure: {str(e)}"}
