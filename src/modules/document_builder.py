from src.utils.return_responses import *
from src.utils.style_output import *

class DocumentBuilder:
    def build_document(self, data_generative_ai: str, document_output_path: str) -> dict:
        try:      
            with open(document_output_path, 'w') as file:
                file.write(data_generative_ai)
            
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Document successfully built')

        except KeyboardInterrupt:
            interruption_message()
