from src.utils.return_responses import *
from src.utils.style_output import *

from weasyprint import HTML
from time import sleep
import markdown
import sys

class ConvertDocument:
    def __init__(self) -> None:
        self.html_content: str = None
    def markdown_to_pdf(self, input_document_path: str, output_document_path: str) -> dict:
        try:
            sleep(2)
            print(f'\n{BLUE}[+]{RESET} Converting Markdown to PDF')
            with open(input_document_path, 'r') as file:
                md_content = file.read()

                self.html_content = markdown.markdown(md_content)
                HTML(string=self.html_content).write_pdf(output_document_path)

            return create_success_return_response(f'\n{GREEN}[v]{RESET} Markdown successfully converted to PDF', self.html_content)
            
        except KeyboardInterrupt:
            print(f'\n{ORANGE}[!]{RESET} Operation interrupted by user')
            sys.exit(0)

        except Exception:
            print(f'\n{RED}[x]{RESET} Failed to convert Markdown to PDF')
