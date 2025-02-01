from src.utils.return_responses import *
from src.utils.style_output import *

from weasyprint import HTML
import markdown

class ConvertDocument:
    def markdown_to_pdf(self, input_document_path: str, output_document_path: str) -> dict:
        try:
            with open(input_document_path, 'r', encoding='utf-8') as file:
                md_content = file.read()

            HTML(string=markdown.markdown(md_content)).write_pdf(output_document_path)

            return create_success_return_response(f'\n{GREEN}[v]{RESET} Markdown successfully converted to PDF')
            
        except KeyboardInterrupt:
            interruption_message()
