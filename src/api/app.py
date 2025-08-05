from src.modules.audio_downloader import AudioDownloader
from src.modules.audio_recognition import AudioRecognition
from src.modules.generative_ai import GenerativeAI
from src.modules.document_builder import DocumentBuilder
from src.modules.convert_document import ConvertDocument
from src.modules.extract_text import ExtractText

from config.prompt_config import prompt_ptBR, prompt_enUS, prompt_questions

from src.utils.send_email_verification import SendEmailVerification
from src.utils.system_utils import clean_up, is_valid_email, validate_user_data

from docs.flasgger import init_flasgger

from flask import Flask, request, jsonify, send_file, Response
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from flask_cors import CORS

from pymongo.collection import Collection
from pymongo import MongoClient

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import speech_recognition as sr
from dotenv import load_dotenv
from threading import Lock
import requests
import datetime
import yt_dlp
import string
import random
import magic
import json
import os
import re

load_dotenv()

class Server:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)

        self.app.config['JWT_SECRET_KEY'] = os.getenv('jwt_secret_key')
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=15)
        self.app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)
        self.app.config['RATELIMIT_STORAGE_URI'] = os.getenv("redis://localhost:6379")


        self.jwt: JWTManager = JWTManager(self.app)
        client = MongoClient(os.getenv('mongodb_key'))
        db = client['lectify-flask-api']
        
        self.check_email_register_collection: Collection = db["check_email_register"]
        self.check_email_register_collection.create_index("timestamp", expireAfterSeconds=600)
        self.check_email_register_collection.create_index("email", unique=True)

        self.check_email_reset_password_collection: Collection = db["check_email_reset_password"]
        self.check_email_reset_password_collection.create_index("timestamp", expireAfterSeconds=600)
        self.check_email_reset_password_collection.create_index("email", unique=True)
        
        self.users_collection: Collection = db['users']
        self.users_collection.create_index("email", unique=True)
        self.users_collection.create_index("username", unique=True)

        self.limiter: Limiter = Limiter(
            key_func=self.user_or_ip,
            app=self.app,
            default_limits=["100 per minute"],
            storage_uri=os.getenv("redis://localhost:6379")
        )

        self.processing_lock = Lock()
        CORS(self.app)
        
        self.youtube_url: str = None
        self.output_format: str = None
        self.language_select: str = None

        self.required_fields: list['str'] = ['youtube_url', 'output_format', 'language_select']
        self.valid_formats: list['str'] = ['pdf', 'md']
        self.valid_languages_formats: list['str'] = ['pt-BR', 'en-US']

        self.expected_mime_types: dict[str, str] = {
            'md': 'text/markdown',
            'pdf': 'application/pdf'
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

        self.prompt: str = None

        self._register_routes()
        init_flasgger(self.app)
    
    def reset_values(self) -> None:
        self.youtube_url: str = None
        self.output_format: str = None
        self.language_select: str = None

        self.file_root_markdown: str = None
        self.file_root_pdf: str = None
        self.file_root_audio: str = None

        self.filepath_secure: str = None

        self.prompt: str = None

    def get_user(self, username) -> dict | None:
        return self.users_collection.find_one({"username": username})
    
    def get_email(self, email) -> dict | None:
        return self.users_collection.find_one({"email": email})
    
    def generate_code(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)).strip()
    
    def is_email_verified(self, email) -> bool:
        return self.check_email_register_collection.find_one({
            "email": email,
            "is_verified": True}) is not None
    
    def user_is_free(self, username: str) -> bool:
        user = self.get_user(username)
        return user.get('is_free', True) if user else True

    def dynamic_limit(self) -> str | None:
        username = get_jwt_identity()
        return "1 per day" if self.user_is_free(username) else None
    
    def user_or_ip(self) -> str:
            try:
                verify_jwt_in_request()
                identity = get_jwt_identity()
                if identity:
                    return identity
            
            except Exception:
                pass
            
            return get_remote_address()

    def create_error_response(self, message: str, code: int) -> Response:
        return jsonify({'error': message}), code

    def _register_routes(self) -> None:
        @self.app.route('/lectify/current_plan', methods=['GET'])
        @jwt_required()
        def current_plan() -> Response:
            username = get_jwt_identity()
            is_free = self.user_is_free(username)
            plan = "free" if is_free else "premium"
            
            return jsonify({"username": username, "plan": plan})
        
        @self.app.errorhandler(429)
        def ratelimit_error(e) -> Response:
            endpoint = request.endpoint
            if endpoint == 'lectify_summarize' or endpoint == 'lectify_questions':
                return self.create_error_response("Daily limit of 5 requests reached.", 429)

            return self.create_error_response("Too many requests. Please try again later.", 429)
                
        @self.app.route('/lectify/summarize', methods=['POST'])
        @jwt_required()
        @self.limiter.limit(lambda: self.dynamic_limit())
        def lectify_summarize() -> Response:
            current_user = get_jwt_identity()
            if not current_user:
                return self.create_error_response("Unauthorized", 401)
            
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
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
                self.language_select = data.get('language_select')
                
                if not self.youtube_url:
                    return self.create_error_response('Missing YouTube URL', 400)
                
                if len(self.youtube_url) > self.max_url_length:
                    return self.create_error_response(f'URL exceeds maximum length of {self.max_url_length} characters', 400)

                if not re.match(self.youtube_regex, self.youtube_url):
                    return self.create_error_response('Invalid YouTube URL', 400)

                if self.output_format not in self.valid_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_formats)}", 400)
                
                if not self.language_select:
                    return self.create_error_response('Missing language selection', 400)
                
                if self.language_select not in self.valid_languages_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_languages_formats)}", 400)

                match self.language_select:
                    case 'pt-BR':
                        self.prompt = prompt_ptBR
                        
                    case 'en-US':
                        self.prompt = prompt_enUS

                try:
                    response_audio_downloader = AudioDownloader().download_audio(self.youtube_url)
                    
                    relative_path_audio = response_audio_downloader['data']
                    relative_path_markdown = f'{relative_path_audio.replace(".wav", "")}.md'
                    relative_path_pdf = f'{relative_path_markdown.replace(".md", "")}.pdf'
                    
                    self.file_root_audio = os.path.abspath(relative_path_audio)
                    self.file_root_markdown = os.path.abspath(relative_path_markdown)
                    self.file_root_pdf = os.path.abspath(relative_path_pdf)
                    
                    try:
                        response_audio_recognition = AudioRecognition().recognize_audio(relative_path_audio, self.language_select)
                        data_value_audio_recognition = response_audio_recognition['data']
                        merged_prompt = f'{self.prompt}\n{data_value_audio_recognition}'
                        
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
                self.processing_lock.release()
        
        @self.app.route('/lectify/questions', methods=['POST'])
        @jwt_required()
        @self.limiter.limit(lambda: self.dynamic_limit())
        def lectify_questions() -> Response:
            current_user = get_jwt_identity()
            
            if not current_user:
                return self.create_error_response("Unauthorized", 401)
            
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
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
                            response_extract_text_markdown = ExtractText().extract_text_markdown(self.filepath_secure)
                            data_value_extract_text_markdown = response_extract_text_markdown['data']
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
                            response_extract_text_pdf = ExtractText().extract_text_pdf(self.filepath_secure)
                            data_value_extract_text_pdf = response_extract_text_pdf['data']
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
                self.processing_lock.release()

        @self.app.route('/lectify/check_email_register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_check_email_register() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                data = request.get_json()
                email = data.get("email").lower().strip()

                if not email:
                    return self.create_error_response("Email is required", 400)
                
                if not is_valid_email(email):
                    return self.create_error_response("Invalid email format", 400)
                
                code = self.generate_code()
                
                self.check_email_register_collection.update_one({
                    "email":email},
                    {
                        "$set": {
                            "is_verified": False,
                            "code": code,
                            "timestamp": datetime.datetime.utcnow()
                        }
                    },
                    upsert=True
                )

                SendEmailVerification().send_verification_email(email, code)

                return jsonify({"message": "Verification code sent to email",}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/verify_email_register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_verify_email_register() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                data = request.get_json()

                email = data.get("email").lower().strip()
                code = data.get("code").upper().strip()

                if not email or not code:
                    return self.create_error_response("Email and code are required", 400)
                
                if not is_valid_email(email):
                    return self.create_error_response("Invalid email format", 400)
                
                check_email_data = self.check_email_register_collection.find_one({"email": email})

                if not check_email_data:
                    return self.create_error_response("Email not found", 404)
                
                validation_error = validate_user_data({
                    "code": code
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                if check_email_data['code'] != code:
                    return self.create_error_response("Invalid verification code", 400)
                
                self.check_email_register_collection.update_one(
                    {"email": email},
                    {"$set": {"is_verified": True}})

                return jsonify({"message": "Email verified successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()

        @self.app.route('/lectify/register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_register() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                data = request.get_json()

                username = data.get("username").lower().strip()
                password = data.get("password").strip()
                email = data.get("email").lower().strip()
                firstname = data.get("firstname").strip().capitalize()
                lastname = data.get("lastname").strip().capitalize()
                
                if not username or not password or not email or not firstname or not lastname:
                    return self.create_error_response("Username, password, email, firstname and lastname are required", 400)
                
                if self.get_user(username):
                    return self.create_error_response("Username already exists", 400)
                
                if self.get_email(email):
                    return self.create_error_response("Email already exists", 400)
                
                if not self.is_email_verified(email):
                    return self.create_error_response("Email not verified", 400)
                
                validation_error = validate_user_data({
                    "username": username,
                    "password": password,
                    "firstname": firstname,
                    "lastname": lastname
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                hashed_password = generate_password_hash(password)
                
                user_data = {
                    "username": username,
                    "password": hashed_password,
                    "email": email,
                    "firstname": firstname,
                    "lastname": lastname,
                    "is_free": True
                }

                self.users_collection.insert_one(user_data)

                return jsonify({"message": "User registered successfully"}), 201
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()

        @self.app.route('/lectify/login', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_login() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                data = request.get_json()

                username = data.get("username").lower().strip()
                password = data.get("password")

                if not username or not password:
                    return self.create_error_response("Username and password are required", 400)
                
                validation_error = validate_user_data({
                    "username": username,
                    "password": password
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                user = self.get_user(username)

                if not user or not check_password_hash(user['password'], password):
                    return self.create_error_response("Invalid username or password", 401)

                access_token = create_access_token(identity=username)
                refresh_token = create_refresh_token(identity=username)

                return jsonify({
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }), 200
            
            except Exception as e:
                return self.create_error_response(f'{e}An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/profile', methods=['GET'])
        @jwt_required()        
        def lectify_profile() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                current_username = get_jwt_identity()
                current_user = self.get_user(current_username)
                
                if not current_user:
                    return self.create_error_response("User not found", 404)
                
                profile_data = {
                    "username": current_user['username'],
                    "email": current_user['email'],
                    "firstname": current_user['firstname'],
                    "lastname": current_user['lastname']
                }

                return jsonify(profile_data), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/refresh_token', methods=['POST'])
        @jwt_required(refresh=True)
        @self.limiter.limit("5 per minute")
        def lectify_refresh_token() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                current_user = get_jwt_identity()

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)
                
                new_access_token = create_access_token(identity=current_user)

                return jsonify({
                    "access_token": new_access_token
                    }), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/update_profile', methods=['POST'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_update_profile() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                current_username = get_jwt_identity()
                current_user = self.get_user(current_username)
                
                if not current_user:
                    return self.create_error_response("User not found", 404)
                
                data = request.get_json()

                update_fields = {}

                if "firstname" in data:
                    if not data['firstname'].strip():
                        return self.create_error_response("Firstname cannot be empty", 400)
                    
                    update_fields['firstname'] = data['firstname'].strip().capitalize()
                
                if "lastname" in data:
                    if not data['lastname'].strip():
                        return self.create_error_response("Lastname cannot be empty", 400)
                    
                    update_fields['lastname'] = data['lastname'].strip().capitalize()
                
                if "password" in data:
                    if not data['password'].strip():
                        return self.create_error_response("Password cannot be empty", 400)
                    
                    new_password = data['password'].strip()
                
                if not update_fields:
                    return self.create_error_response("No fields to update", 400)
                
                validation_error = validate_user_data({
                    "password": new_password if "password" in data else None,
                    "firstname": update_fields.get('firstname'),
                    "lastname": update_fields.get('lastname')
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                if "password" in data:
                    update_fields['password'] = generate_password_hash(new_password)
                
                self.users_collection.update_one({"username": current_username}, {"$set": update_fields})
                
                return jsonify({"message": "Profile updated successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/delete_account', methods=['DELETE'])
        @jwt_required()
        @self.limiter.limit("1 per minute")
        def lectify_delete_account() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                current_username = get_jwt_identity()
                current_user = self.get_user(current_username)
                
                if not current_user:
                    return self.create_error_response("User not found", 404)
                
                self.users_collection.delete_one({"username": current_username})

                return jsonify({"message": "Account deleted successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/check_email_reset_password', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_check_email_reset_password() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                data = request.get_json()
                email = data.get("email").lower().strip()

                if not email:
                    return self.create_error_response("Email is required", 400)
                
                if not self.get_email(email):
                    return self.create_error_response("Email not found", 404)
                
                code = self.generate_code()
                
                self.check_email_reset_password_collection.update_one({
                    "email": email},
                    {
                        "$set": {
                            "is_verified": False,
                            "code": code,
                            "timestamp": datetime.datetime.utcnow()
                        }
                    },
                    upsert=True
                )

                SendEmailVerification().send_verification_email(email, code)

                return jsonify({"message": "Password reset code sent to email"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()
        
        @self.app.route('/lectify/verify_email_reset_password', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_verify_email_reset_password() -> Response:
            if not self.processing_lock.acquire(blocking=False):
                return self.create_error_response("Server busy. Please try again shortly", 429)
            
            try:
                data = request.json
                email = data.get("email").lower().strip()
                code = data.get("code").upper().strip()
                new_password = data.get("new_password")

                if not email or not code or not new_password:
                    return self.create_error_response("Email, code, and new password are required", 400)
                
                validation_error = validate_user_data({
                    "email": email,
                    "password": new_password,
                    "code": code
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                check_email_data = self.check_email_reset_password_collection.find_one({"email": email})

                if not check_email_data:
                    return self.create_error_response("Email not found", 404)

                if check_email_data['code'] != code:
                    return self.create_error_response("Invalid verification code", 400)
                
                hashed_password = generate_password_hash(new_password)
                self.users_collection.update_one(
                    {"email": email},
                    {"$set": {"password": hashed_password}})

                self.check_email_reset_password_collection.delete_one({"email": email})

                return jsonify({"message": "Password reset successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
            
            finally:
                self.processing_lock.release()

    def run_production(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        self.app.run(debug=False, host=host, port=port, use_reloader=False)