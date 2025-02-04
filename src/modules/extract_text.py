from src.utils.return_responses import *
from src.utils.style_output import *

from bs4 import BeautifulSoup
import pdfplumber
import markdown

class ExtractText:
    def extract_text_markdown(self, md_path: str) -> dict:
        try:
            with open(md_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            html_content = markdown.markdown(md_content)
            text = BeautifulSoup(html_content, 'html.parser').get_text()
            
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Text successfully extracted from Markdown', text)
        
        except KeyboardInterrupt:
            interruption_message()

    def extract_text_pdf(self, pdf_path: str) -> dict:
        try:
            with pdfplumber.open(pdf_path) as file:
                text = ''
                for page in file.pages:
                    text += page.extract_text()

            return create_success_return_response(f'\n{GREEN}[v]{RESET} Text successfully extracted from PDF', text)
        
        except KeyboardInterrupt:
            interruption_message()
