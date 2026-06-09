from src.utils.return_responses import create_success_return_response

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

class GenerativeAI:
    def __init__(self) -> None:
        self.api_key = os.getenv("API_KEY_GENERATIVEAI")
        self.client = genai.Client(api_key=self.api_key)

        self.generation_config = {
            "temperature": 0,
            "top_p": 0.9,
            "top_k": 40,
        }

    def start_chat(self, input_text: str) -> dict:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=input_text,
            config=self.generation_config
        )
        
        return create_success_return_response("Successfully processed the Generative AI response", response.text)