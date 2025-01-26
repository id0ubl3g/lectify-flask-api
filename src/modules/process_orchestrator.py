import sys
import os

def add_project_root_to_path() -> None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
add_project_root_to_path()

from src.modules.audio_downloader import AudioDownloader
from src.modules.audio_recognition import AudioRecognition
from src.modules.generative_ai import GenerativeAI
from src.modules.document_builder import DocumentBuilder
from src.modules.convert_document import ConvertDocument

from src.utils.style_output import *

from config.prompt_config import *

class ProcessOrchestrator:
    def __init__(self) -> None:
        self.response_audio_path_downloader: str = None
        self.response_audio_recognized: str =  None
        self.response_data_generative_ai: str = None
        self.response_document_output_path: str = None
        self.response_output_document_converted_path: str = None

    def process_audio_downloader(self, youtube_url: str) -> None:
        try:
            response_audio_downloader: dict = AudioDownloader().download_audio(youtube_url)
            print(response_audio_downloader['message'])
            self.response_audio_path_downloader = response_audio_downloader['data']

            return
    
        except KeyboardInterrupt:
            interruption_message()

        except Exception:
            exception_error('audio downloading')

    def process_audio_recognition(self, audio_path: str) -> None:
        try:
            response_audio_recognition: dict = AudioRecognition().recognize_audio(audio_path)
            print(response_audio_recognition['message'])
            self.response_audio_recognized = response_audio_recognition['data']

            return

        except KeyboardInterrupt:
            interruption_message()

        except Exception:
            exception_error('audio recognition')

    def process_generative_ai(self, input_text: str) -> None:
        try:
            response_generative_ai: dict = GenerativeAI().start_chat(input_text)
            print(response_generative_ai['message'])
            self.response_data_generative_ai = response_generative_ai['data']
            
            return
        
        except KeyboardInterrupt:
            interruption_message()

        except Exception:
            exception_error('Generative AI processing')
    
    def process_document_builder(self, data_generative_ai: str) -> None:
        try:
            self.response_document_output_path = f'{self.response_audio_path_downloader.replace(".wav", "")}(Lectify).md'
            response_document_builder = DocumentBuilder().build_document(data_generative_ai, self.response_document_output_path)
            print(response_document_builder['message'])

            return
        
        except KeyboardInterrupt:
            interruption_message()

        except Exception:
            exception_error('document building')

    def process_convert_document(self, input_document_path: str) -> None:
        try:
            self.response_output_document_converted_path = f'{self.response_document_output_path.replace(".md", "")}.pdf'
            response_document_convert = ConvertDocument().markdown_to_pdf(input_document_path, self.response_output_document_converted_path)
            print(response_document_convert['message'])

            return
        
        except KeyboardInterrupt:
            interruption_message()

        except Exception:
            exception_error('document conversion')

    def process_workflow(self, youtube_url: str) -> None:
        try:
            self.process_audio_downloader(youtube_url)
            self.process_audio_recognition(self.response_audio_path_downloader)
            merged_prompt = f'{prompt}\n{self.response_audio_recognized}'
            self.process_generative_ai(merged_prompt)
            self.process_document_builder(self.response_data_generative_ai)
            self.process_convert_document(self.response_document_output_path)
        
        except KeyboardInterrupt:
            interruption_message()

        except Exception:
            exception_error('workflow')
