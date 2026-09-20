from src.utils.return_responses import create_success_return_response
from src.utils.system_utils import google_credentials_path

from google.oauth2 import service_account
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

class Vertex:
    def __init__(self) -> None:
        credentials = service_account.Credentials.from_service_account_file(
            google_credentials_path(),
            scopes=["https://www.googleapis.com/auth/cloud-platform"])

        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            credentials=credentials
        )

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