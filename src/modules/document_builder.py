from src.utils.return_responses import *
from src.utils.style_output import *

class DocumentBuilder:
    def __init__(self) -> None:
        self.temporary_path = '/src/temp/'
        
    def build_document(self, data_generative_ai: str, document_output_path: str) -> dict:
        try:      
            with open(document_output_path, 'w') as file:
                file.write(data_generative_ai)
            
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Document successfully built', document_output_path)

        except KeyboardInterrupt:
            interruption_message()
        
        except OSError:
            custom_error_message('OS error occurred while handling the file')

        except Exception:
            exception_error('document building')
        