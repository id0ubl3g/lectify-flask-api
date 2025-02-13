from src.modules.audio_downloader import AudioDownloader
from src.modules.audio_recognition import AudioRecognition
from src.modules.generative_ai import GenerativeAI
from src.modules.document_builder import DocumentBuilder
from src.modules.convert_document import ConvertDocument
from src.modules.extract_text import ExtractText

from config.prompt_config import prompt_questions, prompt

from src.utils.system_utils import clean_up

from docs.flasgger import init_flasgger

from flask import Flask, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import speech_recognition as sr
from flask_cors import CORS
import requests
import yt_dlp
import magic
import json
import os
import re

class Server:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)
        CORS(self.app)
        
        self.youtube_url: str = None
        self.output_format: str = None

        self.required_fields: list['str'] = ['youtube_url', 'output_format']
        self.valid_formats: list['str'] = ['pdf', 'md']

        self.expected_mime_types: dict[str, str] = {
            'md': 'text/markdown',
            'pdf': 'application/pdf',
        }

        self.blocked_extensions: frozenset[str] = frozenset({
            '.py', '.sh', '.bat', '.cmd', '.ps1', '.exe', '.js',
            '.msi', '.vbs', '.wsf', '.jar', '.scr', '.cpl',
            '.hta', '.wsh', '.scf', '.lnk', '.reg', '.inf',
            '.iso', '.dmg',
            '.docm', '.xlsm', '.pptm',
            '.dotm', '.xltm', '.ppsm',
            '.odt',                                              
            '.zip', '.tar', '.tar.gz', '.rar', '.7z',
            '.apk',
            '.dll', '.drv', '.vxd', '.sys',
            '.bak', '.old', '.swp',
            '.chm', '.mdb', '.sql', '.db'
        })

        self.output_path: str = 'src/temp'
        self.filepath_secure: str = None

        self.file_root_markdown: str = None
        self.file_root_pdf: str = None
        self.file_root_audio: str = None

        self.youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/)?[a-zA-Z0-9_-]{11}')
        self.max_url_length: int = 200

        self._register_routes()
        init_flasgger(self.app)
    
    def reset_values(self) -> None:
        self.youtube_url: str = None
        self.output_format: str = None

        self.file_root_markdown: str = None
        self.file_root_pdf: str = None
        self.file_root_audio: str = None

        self.filepath_secure: str = None

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
                    
                    relative_path_audio = response_audio_downloader['data']
                    relative_path_markdown = f'{relative_path_audio.replace(".wav", "")}.md'
                    relative_path_pdf = f'{relative_path_markdown.replace(".md", "")}.pdf'
                    
                    self.file_root_audio = os.path.abspath(relative_path_audio)
                    self.file_root_markdown = os.path.abspath(relative_path_markdown)
                    self.file_root_pdf = os.path.abspath(relative_path_pdf)
                    
                    try:
                        response_audio_recognition = AudioRecognition().recognize_audio(relative_path_audio)
                        data_value_audio_recognition = response_audio_recognition['data']
                        merged_prompt = f'{prompt}\n{data_value_audio_recognition}'
                        
                        try:
                            response_generative_ai = GenerativeAI().start_chat(merged_prompt)
                            
                            try:
                                DocumentBuilder().build_document(response_generative_ai['data'], relative_path_markdown)
                                
                                try:
                                    ConvertDocument().markdown_to_pdf(relative_path_markdown, relative_path_pdf)

                                    match self.output_format:
                                        case 'md':
                                            return send_file(self.file_root_markdown, mimetype='text/markdown', as_attachment=True), 201
                                        
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
        
        @self.app.route('/lectify/questions', methods=['POST'])
        def lectify_questions() -> Response:
            try:
                received_file = request.files['file']

                if not received_file:
                    return self.create_error_response('No files received', 400)

                file_size_bytes = len(received_file.read())
                received_file.seek(0)
                file_size_mb = (file_size_bytes / 1024) / 1024

                if file_size_mb > 5:
                    return self.create_error_response('File size exceeds the maximum limit of 5 MB.', 413)

                if not os.path.exists(self.output_path):
                    os.makedirs(self.output_path)
                
                filename_nosecure = received_file.filename
                filename_secure = secure_filename(filename_nosecure)
                self.filepath_secure = os.path.join(self.output_path, filename_secure)

                if len(filename_secure) > 200:
                    return self.create_error_response('File name exceeds the maximum length of 100 characters.', 400)

                file_extension = self.filepath_secure.split('.')[-1].lower()

                if file_extension not in self.valid_formats:
                    return self.create_error_response(f'Invalid format. Supported formats: {", ".join(self.valid_formats)}', 400)
                
                received_file.save(self.filepath_secure)

                for extensions in self.blocked_extensions:
                    if extensions in filename_secure:
                        return self.create_error_response(f'The filename seems suspicious and contains a blocked extension: {extensions}', 400)
                
                mime_detector = magic.Magic(mime=True)
                expected_mime_type = self.expected_mime_types.get(file_extension)
                detected_mime_type = mime_detector.from_file(self.filepath_secure)
                
                if expected_mime_type == 'text/markdown':
                    detected_mime_type = expected_mime_type
                
                if detected_mime_type != expected_mime_type:
                    return self.create_error_response(f'Invalid file type. Detected: {detected_mime_type}. Expected: {expected_mime_type}', 400)

                match file_extension:
                    case 'md':
                        try:
                            responde_extract_text_markdown = ExtractText().extract_text_markdown(self.filepath_secure)
                            data_value_extract_text_markdown = responde_extract_text_markdown['data']
                            merged_prompt_questions = f'{prompt_questions}\n{data_value_extract_text_markdown}'
                            
                            try:
                                response_generative_ai = GenerativeAI().start_chat(merged_prompt_questions)

                                response_generative_ai_json = json.loads(response_generative_ai['data'])
                                
                                return jsonify(response_generative_ai_json), 200
                            
                            except Exception:
                                return self.create_error_response("Error during chat generation", 400)
                        
                        except Exception:
                            return self.create_error_response('Error during extraction of Markdown text', 400)

                    case 'pdf':
                        try:
                            responde_extract_text_pdf = ExtractText().extract_text_pdf(self.filepath_secure)
                            data_value_extract_text_pdf = responde_extract_text_pdf['data']
                            merged_prompt_questions = f'{prompt_questions}\n{data_value_extract_text_pdf}'
                            
                            try:
                                response_generative_ai = GenerativeAI().start_chat(merged_prompt_questions)

                                response_generative_ai_json = json.loads(response_generative_ai['data'])
                                return jsonify(response_generative_ai_json), 200

                            except Exception:
                                return self.create_error_response("Error during chat generation", 400)

                        except Exception:
                            return self.create_error_response('Error during extraction of PDF text', 400)
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                clean_up(self.filepath_secure)
                self.reset_values()

    def run_production(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        self.app.run(debug=False, host=host, port=port, use_reloader=False)

