from src.utils.return_responses import create_success_return_response

class DocumentBuilder:
    def build_document(self, data_generative_ai: str, document_output_path: str) -> dict:
        with open(document_output_path, 'w', encoding='utf-8') as file:
            if data_generative_ai.startswith("```markdown"):
                data_generative_ai = data_generative_ai.removeprefix("```markdown").strip()

            elif data_generative_ai.startswith("```"):
                data_generative_ai = data_generative_ai.removeprefix("```").strip()

            if data_generative_ai.endswith("```"):
                data_generative_ai = data_generative_ai.removesuffix("```").strip()
                
            file.write(data_generative_ai)
        
        return create_success_return_response(f'Markdown document successfully built')