from src.utils.return_responses import *
from src.utils.style_output import *

import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any
from time import sleep
import sys
import os

load_dotenv()

class GenerativeAI:
    def __init__(self) -> None:
        self.api_key: str = os.getenv("api_key_generativeai")
        genai.configure(api_key=self.api_key)

        os.environ["GRPC_VERBOSITY"] = "NONE"
        
        self.generation_config:  Dict[str, object] = {
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                    "response_mime_type": "text/plain",
                }
        
        try:
            sleep(2)
            print(f'\n{BLUE}[+]{RESET} Initializing GenerativeModel')
            
            self.model: Any = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=self.generation_config
            )

            sleep(2)
            print(f'\n{GREEN}[v]{RESET} GenerativeModel initialized')
        
        except Exception:
            print(f'\n{RED}[x]{RESET} Failed to initialize GenerativeModel')

    def start_chat(self, input_text: str) -> dict:
        try:
            sleep(2)
            print(f'\n{BLUE}[+]{RESET} Processing the Generative AI response')
            chat_session = self.model.start_chat(
                history=[]
            )
            response_generative_ai = chat_session.send_message(input_text)
            
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Successfully processed the Generative AI response', response_generative_ai.text)
        
        except KeyboardInterrupt:
            print(f'\n{ORANGE}[!]{RESET} Operation interrupted by user')
            sys.exit(0)
        
        except Exception:
            return create_error_return_response(f'\n{RED}[x]{RESET} Error during chat generation')
