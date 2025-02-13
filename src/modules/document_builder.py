from src.utils.return_responses import create_success_return_response

class DocumentBuilder:
    def build_document(self, data_generative_ai: str, document_output_path: str) -> dict:
        with open(document_output_path, 'w', encoding='utf-8') as file:
            file.write(data_generative_ai)
        
        return create_success_return_response(f'Markdown document successfully built')

