from src.utils.return_responses import *

from weasyprint import HTML
import markdown

class ConvertDocument:
    def markdown_to_pdf(self, input_document_path: str, output_document_path: str) -> dict:
        with open(input_document_path, 'r', encoding='utf-8') as file:
            md_content = file.read()

        HTML(string=markdown.markdown(md_content)).write_pdf(output_document_path)

        return create_success_return_response(f'Markdown successfully converted to PDF')
