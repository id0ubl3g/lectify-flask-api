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

from src.utils.system_utils import *
from src.utils.style_output import *

from config.prompt_config import *

from flask import Flask, request, jsonify, send_file, Response
from typing import List, Optional
import speech_recognition as sr
from flask_cors import CORS
import requests
import yt_dlp
import re

class Server:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)
        CORS(self.app)
        
        self.youtube_url: Optional[str] = None
        self.output_format: Optional[str] = None

        self.required_fields: List['str'] = ['youtube_url', 'output_format']
        self.valid_formats: List['str'] = ['pdf', 'md']

        self.file_root_markdown: str = None
        self.file_root_pdf: str = None
        self.file_root_audio: str = None

        self.youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/)?[a-zA-Z0-9_-]{11}')
        self.max_url_length = 200

        self._register_routes()
    
    def reset_values(self):
        self.youtube_url: Optional[str] = None
        self.output_format: Optional[str] = None

        self.file_root_markdown: str = None
        self.file_root_pdf: str = None
        self.file_root_audio: str = None

    def create_error_response(self, message: str, code: int) -> Response:
        return jsonify({'error': message}), code

    def _register_routes(self) -> None:
        @self.app.route('/lectify/summarize', methods=['POST'])
        def lectify_summarize() -> Response:
            try:
                data = request.get_json()
                
                if not data:
                    return self.create_error_response('No data provided', 400)
                
                missing_fields = [field for field in self.required_fields if field not in data]
                if missing_fields:
                    missing_fields_str = ', '.join(missing_fields)
                    return self.create_error_response(f"Missing required fields: {missing_fields_str}", 400)
                
                self.youtube_url = data.get('youtube_url')
                self.output_format = data.get('output_format')

                if not self.youtube_url:
                    return self.create_error_response('Missing YouTube URL', 400)
                
                if len(self.youtube_url) > self.max_url_length:
                    return self.create_error_response(f'URL exceeds maximum length of {self.max_url_length} characters', 400)

                if not re.match(self.youtube_regex, self.youtube_url):
                    return self.create_error_response('Invalid YouTube URL', 400)

                if self.output_format not in self.valid_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_formats)}", 400)

                try:
                    response_audio_downloader = AudioDownloader().download_audio(self.youtube_url)
                    print(response_audio_downloader['message'])
                    
                    relative_path_audio = response_audio_downloader['data']
                    relative_path_markdown = f'{relative_path_audio.replace(".wav", "")}.md'
                    relative_path_pdf = f'{relative_path_markdown.replace(".md", "")}.pdf'
                    
                    self.file_root_audio = os.path.abspath(relative_path_audio)
                    self.file_root_markdown = os.path.abspath(relative_path_markdown)
                    self.file_root_pdf = os.path.abspath(relative_path_pdf)
                    try:
                        response_audio_recognition = AudioRecognition().recognize_audio(relative_path_audio)
                        merged_prompt = f'{prompt}\n{response_audio_recognition['data']}'
                        print(response_audio_recognition['message'])
                        try:
                            response_generative_ai = GenerativeAI().start_chat(merged_prompt)
                            print(response_generative_ai['message'])
                            try:
                                response_document_builder = DocumentBuilder().build_document(response_generative_ai['data'], relative_path_markdown)
                                print(response_document_builder['message'])
                                try:
                                    response_convert_document = ConvertDocument().markdown_to_pdf(relative_path_markdown, relative_path_pdf)
                                    print(response_convert_document['message'])

                                    match self.output_format:
                                        case 'md':
                                            return send_file(self.file_root_markdown, as_attachment=True), 201
                                        
                                        case 'pdf':
                                            return send_file(self.file_root_pdf, as_attachment=True), 201
                                
                                except FileNotFoundError:
                                    return self.create_error_response('File not found', 400)

                                except Exception:
                                    return self.create_error_response('Error during document conversion', 400)

                            except OSError:
                                return self.create_error_response('OS error occurred while handling the file', 400)

                            except Exception:
                                return self.create_error_response('Error during document building', 400)

                        except Exception:
                            return self.create_error_response("Error during chat generation", 400)
                    
                    except sr.UnknownValueError:
                        return self.create_error_response('Unable to understand the audio', 400)
            
                    except sr.RequestError:
                        return self.create_error_response('Error in service request', 400)
                    
                    except Exception:
                        return self.create_error_response('Error during audio recognition', 400)

                except yt_dlp.utils.DownloadError:
                    return self.create_error_response('Download error occurred. Please check the URL and your network connection', 400)
        
                except requests.exceptions.RequestException:
                    return self.create_error_response('Network error. Please check your internet connection', 400)

                except Exception:
                    return self.create_error_response('Error during audio downloading', 400)

            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

            finally:
                clean_up(self.file_root_markdown, self.file_root_pdf, self.file_root_audio)
                self.reset_values()
                
    def run_development(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        welcome_message()
        self.app.run(debug=True, host=host, port=port, use_reloader=True)

