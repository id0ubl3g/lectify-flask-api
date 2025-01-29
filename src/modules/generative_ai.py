from src.utils.return_responses import *
from src.utils.style_output import *

import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Union
import os

load_dotenv()

class GenerativeAI:
    def __init__(self) -> None:
        self.api_key: str = os.getenv('api_key_generativeai')
        genai.configure(api_key=self.api_key)

        os.environ["GRPC_VERBOSITY"] = "NONE"
        
        self.generation_config:  Dict[str, Union[int, float, str]] = {
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                    "response_mime_type": "text/plain",
                }
        
        self.model: genai.GenerativeModel = self._initialize_model()
        
    def _initialize_model(self) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self.generation_config
        )

    def start_chat(self, input_text: str) -> dict:
        try:
            chat_session = self.model.start_chat(history=[])
            response_generative_ai = chat_session.send_message(input_text)
            
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Successfully processed the Generative AI response', response_generative_ai.text)
        
        except KeyboardInterrupt:
            interruption_message()

