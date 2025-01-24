from src.utils.return_responses import *
from src.utils.style_output import *

from time import sleep
import sys

class DocumentBuilder:
    def __init__(self) -> None:
        self.temporary_path = '/src/temp/'
        
    def build_document(self, data_generative_ai: str, document_output_path: str) -> dict:
        try:
            sleep(2)
            print(f'\n{BLUE}[+]{RESET} Building the document')
            
            with open(document_output_path, 'w') as file:
                file.write(data_generative_ai)
            
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Document successfully built', document_output_path)

        except KeyboardInterrupt:
            print(f'\n{ORANGE}[!]{RESET} Operation interrupted by user')
            sys.exit(1)

        except Exception:
            return create_error_return_response(f'\n{RED}[x]{RESET} Failed to build document')
        