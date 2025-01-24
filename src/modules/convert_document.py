from src.utils.return_responses import *
from src.utils.style_output import *

from weasyprint import HTML
import markdown

class ConvertDocument:
    def __init__(self) -> None:
        self.html_content: str = None
    def markdown_to_pdf(self, input_document_path: str, output_document_path: str) -> dict:
        try:
            with open(input_document_path, 'r') as file:
                md_content = file.read()

            self.html_content = markdown.markdown(md_content)
            HTML(string=self.html_content).write_pdf(output_document_path)

            return create_success_return_response(f'\n{GREEN}[v]{RESET} Markdown successfully converted to PDF', self.html_content)
            
        except KeyboardInterrupt:
            interruption_message()

        except FileNotFoundError:
            custom_error_message('File not found')

        except Exception:
            exception_error('document conversion')
