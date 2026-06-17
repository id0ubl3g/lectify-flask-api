from src.modules.generative_ai import GenerativeAI
from src.modules.extract_text import ExtractText

from src.rabbitmq.publisher import publish_message

from config.prompt_config import prompt_questions
from docs.flasgger import init_flasgger
from config.file_config import *
from config.input_config import *

from config.providers.initialize_mongodb import initialize_mongodb
from config.providers.initialize_mercadopago import initialize_mercadopago
from config.providers.initialize_redis  import initialize_redis
from config.providers.initialize_cloudinary  import initialize_cloudinary

from src.utils.send_email_verification import SendEmailVerification
from src.utils.system_utils import clean_up, is_valid_email, validate_user_data, sanitize_filename

from flask import Flask, request, jsonify, send_file, Response
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo.collection import Collection
from datetime import datetime, timezone,timedelta
from dotenv import load_dotenv
import cloudinary.uploader
from bson import ObjectId
import requests
import secrets
import string
import random
import magic
import json
import math
import os
import re

load_dotenv()

class Server:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)

        self.app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        self.app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        self.app.config['RATELIMIT_STORAGE_URI'] = os.getenv("REDIS_URL")

        self.jwt: JWTManager = JWTManager(self.app)

        mongo = initialize_mongodb()
        mercadopago = initialize_mercadopago()
        redis = initialize_redis(self.app, self.user_or_ip)
        self.cloudinary = initialize_cloudinary() 

        self.grid_fs = mongo["grid_fs"]
        self.documents_collection = mongo["documents_collection"]
        self.check_email_collection: Collection = mongo["check_email_collection"]
        self.users_collection: Collection = mongo["users_collection"]
        self.check_summarize_collection: Collection = mongo["check_summarize_collection"]
        
        self.mercadopago_sdk = mercadopago["mercadopago"]
        self.mercadopago_webhook_secret = mercadopago["webhook_secret"]
        self.plans = mercadopago['plans']

        self.redis_client = redis["redis_client"]
        self.limiter = redis["limiter"]

        CORS(
            self.app,
            origins="*",
            allow_headers=["Content-Type", "Authorization"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
        )
                
        self.youtube_url: str = None
        self.output_format: str = None
        self.language_select: str = None

        self.required_fields: list = REQUIRED_FIELDS
        self.valid_formats: list= VALID_FORMATS
        self.valid_languages_formats: list = VALID_LANGUAGE_FORMATS

        self.expected_mime_types: dict = EXPECTED_MIME_TYPES
        self.blocked_extensions: frozenset = BLOCKED_EXTENSIONS
        self.valid_format_images: list = VALID_FORMAT_IMAGES
        self.expected_image_mime_types: dict = EXPECTED_IMAGE_MIME_TYPES

        self.output_path: str = OUTPUT_PATH
        self.filepath_secure: str = None

        self.youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/)?[a-zA-Z0-9_-]{11}')
        self.max_url_length: int = 200

        self._register_routes()
        init_flasgger(self.app)

    def create_error_response(self, message: str, code: int) -> Response:
        return jsonify({'error': message}), code

    def get_user(self, username) -> dict | None:
        return self.users_collection.find_one({"username": username})
    
    def get_email(self, email) -> dict | None:
        return self.users_collection.find_one({"email": email})
    
    def generate_code(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)).strip()

    def generate_hash(self) -> str:
        return secrets.token_hex(32)
    
    def is_email_verified(self, email) -> bool:
        return self.check_email_collection.find_one({
            "email": email,
            "is_verified": True}) is not None
    
    def user_is_free(self, username: str) -> bool:
        current_user = self.get_user(username)

        if not current_user:
            return True

        subscription_end = current_user.get("subscription_end")

        has_active_subscription = (
            subscription_end is not None
            and datetime.now(timezone.utc) < subscription_end
        )

        if has_active_subscription:
            if current_user.get("is_free", True):
                self.users_collection.update_one(
                    {"username": username},
                    {"$set": {"is_free": False}}
                )

            return False

        if not current_user.get("is_free", True):
            self.users_collection.update_one(
                {"username": username},
                {"$set": {"is_free": True}}
            )

        return True
        
    def user_or_ip(self) -> str | None:
            try:
                verify_jwt_in_request()
                identity = get_jwt_identity()
                if identity:
                    return identity
                
            except Exception:
                endpoint = request.endpoint
                endpoints_require = ['lectify_summarize', 'lectify_check_summarize', 'lectify_summarize_files', 
                                    'lectify_summarize_files_by_id', 'lectify_questions','lectify_profile',
                                    'lectify_refresh_token', 'lectify_update_profile', 'lectify_update_image_profile',
                                    'lectify_ping_email_delete_account', 'lectify_pong_email_delete_account','lectify_ping_check_email_reset_password',
                                    'lectify_pong_verify_email_reset_password', 'lectify_checkout']

                if endpoint not in (endpoints_require):
                    return get_remote_address()
                
                return False

    def check_and_apply_block(self, current_user: str, increment: bool = True) -> Response | None:
        block_key = f"blocked:{current_user}"
        count_key = f"count429:{current_user}"
        
        ttl = self.redis_client.ttl(block_key)
        if ttl > 0:
            minutes = max(1, math.ceil(ttl / 60))
            return self.create_error_response(f"You have been temporarily blocked due to repeated rate limit violations. Please try again in {minutes} minute(s).", 403)
        
        count =  None
        
        if increment:
            pipe = self.redis_client.pipeline()
            pipe.incr(count_key)
            pipe.expire(count_key, 300)
            
            count, _ = pipe.execute()

        if increment and count == 3:
            return self.create_error_response("You are approaching the rate limit. One more failed attempt will block you for 30 minutes. Please try again later.", 429)

        if increment and count >= 4:
            self.redis_client.set(block_key, 1, ex=1800)
            self.redis_client.delete(count_key)
            
            return self.create_error_response("You have been temporarily blocked due to repeated rate limit violations.", 403)
        
        return None

    def _register_routes(self) -> None:
        @self.app.errorhandler(429)
        def ratelimit_error(e) -> Response:
            current_user = self.user_or_ip()
            response_check_and_apply_block = self.check_and_apply_block(current_user)

            if response_check_and_apply_block:
                return response_check_and_apply_block

            endpoint = request.endpoint

            if endpoint in ("lectify_summarize", "lectify_questions"):
                if self.user_is_free(current_user):
                    return self.create_error_response("Monthly free plan limit exceeded.", 429)

            return self.create_error_response("Too many requests. Please try again later.", 429)
        
        @self.app.after_request
        def after_request(response) -> Response:
            endpoint = request.endpoint
            if endpoint == 'lectify_questions':
                clean_up(getattr(self, "filepath_secure", None))
            
            return response

        @self.app.route('/lectify/summarize', methods=['POST'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_summarize() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                            
                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                data = request.get_json()
                
                if not data:
                    return self.create_error_response('No data provided', 400)
                
                missing_fields = [field for field in self.required_fields if field not in data]
                if missing_fields:
                    missing_fields_str = ', '.join(missing_fields)
                    return self.create_error_response(f"Missing required fields: {missing_fields_str}", 400)
                
                youtube_url = data.get('youtube_url')
                output_format = data.get('output_format')
                language_select = data.get('language_select')
                
                if not youtube_url:
                    return self.create_error_response('Missing YouTube URL', 400)
                
                if len(youtube_url) > self.max_url_length:
                    return self.create_error_response(f'URL exceeds maximum length of {self.max_url_length} characters', 400)

                if not youtube_url.startswith("https://"):
                    youtube_url = "https://" + youtube_url

                if not re.match(self.youtube_regex, youtube_url):
                    return self.create_error_response('Invalid YouTube URL', 400)
                
                if not output_format:
                    return self.create_error_response('Missing output format', 400)
                
                if output_format not in self.valid_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_formats)}", 400)
                
                if not language_select:
                    return self.create_error_response('Missing language selection', 400)
                
                if language_select not in self.valid_languages_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_languages_formats)}", 400)
                
                status_check_summarize_collection = self.check_summarize_collection.find_one({
                    "username": current_user,
                    "youtube_url": youtube_url,
                    "language_select": language_select,
                    "output_format": output_format,
                    "status": "processing"})
                
                if status_check_summarize_collection:
                    return self.create_error_response("A summarize request is already being processed for this request", 409)
                
                file_documents_collection = self.documents_collection.find_one({
                    "youtube_url": youtube_url,
                    "filetype": output_format,
                    "language": language_select,
                    "username": current_user
                })

                if file_documents_collection:
                    grid_out = self.grid_fs.get(file_documents_collection["_id"])
                    file_data = grid_out.read()
                    filetype = grid_out.filetype
                    mimetype = "application/pdf" if filetype == "pdf" else "text/markdown"

                    return Response(
                            file_data,
                            mimetype=mimetype,
                            headers={
                                "Content-Disposition": f"attachment; filename={sanitize_filename(grid_out.filename)}"
                        }
                    )

                try:
                    publish_message(
                        queue='summarize_queue',
                        message={
                            'youtube_url': youtube_url,
                            'language_select': language_select,
                            'output_format': output_format,
                            'username': current_user
                        }
                    )

                    return jsonify({"message": "Your request has been successfully placed in the RabbitMQ queue and will be processed shortly"}), 200

                except Exception:
                    return self.create_error_response('Error during publishing message to queue in summarize', 500)
                
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/check_summarize', methods=['POST'])
        @jwt_required()
        @self.limiter.limit("20 per minute")
        def lectify_check_summarize() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                
                data = request.get_json()
                
                if not data:
                    return self.create_error_response('No data provided', 400)
                
                missing_fields = [field for field in self.required_fields if field not in data]
                if missing_fields:
                    missing_fields_str = ', '.join(missing_fields)
                    return self.create_error_response(f"Missing required fields: {missing_fields_str}", 400)

                youtube_url = data.get('youtube_url')
                output_format = data.get('output_format')
                language_select = data.get('language_select')

                if not youtube_url:
                    return self.create_error_response('Missing YouTube URL', 400)
                
                if len(youtube_url) > self.max_url_length:
                    return self.create_error_response(f'URL exceeds maximum length of {self.max_url_length} characters', 400)

                if not youtube_url.startswith("https://"):
                    youtube_url = "https://" + youtube_url

                if not re.match(self.youtube_regex, youtube_url):
                    return self.create_error_response('Invalid YouTube URL', 400)
                
                if not output_format:
                    return self.create_error_response('Missing output format', 400)
                
                if output_format not in self.valid_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_formats)}", 400)
                
                if not language_select:
                    return self.create_error_response('Missing language selection', 400)
                
                if language_select not in self.valid_languages_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_languages_formats)}", 400)
                
                status_check_summarize_collection = self.check_summarize_collection.find_one({
                    "username": current_user,
                    "youtube_url": youtube_url,
                    "language_select": language_select,
                    "output_format": output_format
                })

                if not status_check_summarize_collection:
                    return self.create_error_response('queue is empty, summarize not started', 400)
                
                queue_data = {
                    "username": current_user,
                    "youtube_url": youtube_url,
                    "language_select": language_select,
                    "output_format": output_format,
                    "status": status_check_summarize_collection['status']
                }

                return jsonify(queue_data), 200

            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/summarize/files', methods=['GET'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_summarize_files() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                try:
                    file_documents_collection = self.documents_collection.find({
                        "username": current_user
                    })

                    if not file_documents_collection:
                        return self.create_error_response('Documents not found in the database', 400)

                    files = []

                    for file in file_documents_collection:
                        grid_out = self.grid_fs.get(file["_id"])

                        files.append({
                            "id": str(file["_id"]),
                            "filename": grid_out.filename,
                            "youtube_url": grid_out.youtube_url,
                            "filetype": grid_out.filetype,
                            "language": grid_out.language,
                            "username": grid_out.username,
                            "summary_at": grid_out.summary_at,
                        })

                    return jsonify(files), 200

                except Exception:
                    return self.create_error_response('Error during fetching documents from the database', 400)

            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

                    
        @self.app.route('/lectify/summarize/files/<string:file_id>', methods=['GET'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_summarize_files_by_id(file_id: str) -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                try:
                    file_documents_collection = self.documents_collection.find_one({
                        "_id": ObjectId(file_id)
                    })

                    if not file_documents_collection:
                        return self.create_error_response('Document not found in the database', 400)

                    grid_out = self.grid_fs.get(file_documents_collection["_id"])
                    file_data = grid_out.read()
                    filetype = grid_out.filetype
                    mimetype = "application/pdf" if filetype == "pdf" else "text/markdown"

                    return Response(
                        file_data,
                        mimetype=mimetype,
                        headers={
                                "Content-Disposition": f"attachment; filename={sanitize_filename(grid_out.filename)}"
                        }
                    )
                
                except Exception:
                    return self.create_error_response('Error during fetching document from the database', 400)
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/questions', methods=['POST'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_questions() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                                            
                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
            
                files = request.files.getlist('file')

                if len(files) > 1:
                    return self.create_error_response('Exactly one file must be uploaded', 400)

                received_file = files[0]

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
                    return self.create_error_response('File name exceeds the maximum length of 200 characters.', 400)

                file_extension = self.filepath_secure.split('.')[-1].lower()

                if file_extension not in self.valid_formats:
                    return self.create_error_response(f'Invalid format. Supported formats: {", ".join(self.valid_formats)}', 400)
                
                for extensions in self.blocked_extensions:
                    if extensions in filename_secure:
                        return self.create_error_response(f'The filename seems suspicious and contains a blocked extension: {extensions}', 400)
                
                received_file.save(self.filepath_secure)
                
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
                            data_value_extract_text_markdown = (response_extract_text_markdown.get('data') or '')[:500]
                            if not data_value_extract_text_markdown.strip():
                                return self.create_error_response('No extractable text found in the Markdown file', 400)
                            
                            merged_prompt_questions = f'{prompt_questions}{data_value_extract_text_markdown}'
                            
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
                            data_value_extract_text_pdf = (response_extract_text_pdf.get('data') or '')[:500]
                            if not data_value_extract_text_pdf.strip():
                                return self.create_error_response('No extractable text found in the PDF', 400)
                            
                            merged_prompt_questions = f'{prompt_questions}{data_value_extract_text_pdf}'
                            
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
            
        @self.app.route('/lectify/check_email_register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_check_email_register() -> Response:
            try:
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                                
                data = request.get_json()

                email = (data.get("email") or "").lower().strip()

                if not email:
                    return self.create_error_response("Email is required", 400)
                
                if not is_valid_email(email):
                    return self.create_error_response("Invalid email format", 400)
                
                if self.get_email(email):
                    return self.create_error_response("Email already exists", 400)
                
                code = self.generate_code()
                
                self.check_email_collection.update_one({
                    "email":email},
                    {
                        "$set": {
                            "type_verification": "register",
                            "is_verified": False,
                            "code": code,
                            "timestamp": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )

                SendEmailVerification().send_verification_email(email, code, 'create_account')

                return jsonify({"message": "Verification code sent to email",}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/verify_email_register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_verify_email_register() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                                
                data = request.get_json()

                email = (data.get("email") or "").lower().strip()
                code = (data.get("code") or "").upper().strip()

                if not email or not code:
                    return self.create_error_response("Email and code are required", 400)
                
                if not is_valid_email(email):
                    return self.create_error_response("Invalid email format", 400)
                
                check_email_data = self.check_email_collection.find_one({"email": email})

                if not check_email_data:
                    return self.create_error_response("Email not found", 404)
                
                if check_email_data['type_verification'] != 'register':
                    return self.create_error_response("Invalid verification type", 400)
                
                validation_error = validate_user_data({
                    "code": code
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                if check_email_data['code'] != code:
                    return self.create_error_response("Invalid verification code", 400)
                
                self.check_email_collection.update_one(
                    {"email": email},
                    {"$set": {"is_verified": True}})

                return jsonify({"message": "Email verified successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_register() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                            
                data = request.get_json()

                username = (data.get("username") or "").lower().strip()
                password = (data.get("password") or "").strip()
                email = (data.get("email") or "").lower().strip()
                firstname = (data.get("firstname") or "").strip().capitalize()
                lastname = (data.get("lastname") or "").strip().capitalize()
                
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
                    "is_free": True,
                    "created_at": datetime.now(timezone.utc),
                    "image_profile": ""
                }

                self.users_collection.insert_one(user_data)

                self.check_email_collection.delete_one({"email": email})

                return jsonify({"message": "User registered successfully"}), 201
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/login', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def lectify_login() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                                
                data = request.get_json()

                username = (data.get("username") or "").lower().strip()
                email = (data.get("email") or "").lower().strip()
                password = (data.get("password") or "").strip()

                if email and not is_valid_email(email):
                    return self.create_error_response("Invalid email format", 400)
                
                if not password:
                    return self.create_error_response("Password is required", 400)

                if not username and not email:
                    return self.create_error_response("You must provide either a username or an email", 400)
                
                if email:
                    user_data = self.get_email(email)
                    
                    if not user_data:
                        return self.create_error_response("Invalid email or password", 401)
                    
                    username = user_data['username']

                validation_error = validate_user_data({
                    "username": username,
                    "password": password
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                current_info_user = self.get_user(username)

                if not current_info_user or not check_password_hash(current_info_user['password'], password):
                    return self.create_error_response("Invalid email or password", 401)
                                
                if not current_info_user:
                    return self.create_error_response("User not found", 404)
                
                profile_data = {
                    "username": current_info_user['username'],
                    "email": current_info_user['email'],
                    "firstname": current_info_user['firstname'],
                    "lastname": current_info_user['lastname'],
                    "is_free": current_info_user['is_free'],
                    "created_at": current_info_user['created_at'],
                    "image_profile": current_info_user.get('image_profile', "")
                }

                access_token = create_access_token(identity=username)
                refresh_token = create_refresh_token(identity=username)

                return jsonify({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "profile": profile_data
                }), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/profile', methods=['GET'])
        @jwt_required()
        def lectify_profile() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                                
                user_is_free = self.user_is_free(current_user)
                current_info_user = self.get_user(current_user)
                
                if not current_info_user:
                    return self.create_error_response("User not found", 404)
                                
                profile_data = {
                    "username": current_info_user['username'],
                    "email": current_info_user['email'],
                    "firstname": current_info_user['firstname'],
                    "lastname": current_info_user['lastname'],
                    "is_free": current_info_user['is_free'],
                    "created_at": current_info_user['created_at'],
                    "image_profile": current_info_user.get('image_profile', "")
                }

                if not user_is_free:
                    profile_data["plan"] = current_info_user.get('plan', None)
                    profile_data["subscription_end"] = current_info_user.get('subscription_end', None)

                return jsonify(profile_data), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/refresh_token', methods=['POST'])
        @jwt_required(refresh=True)
        @self.limiter.limit("5 per minute")
        def lectify_refresh_token() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                                                
                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)
                
                new_access_token = create_access_token(identity=current_user)

                return jsonify({
                    "access_token": new_access_token
                    }), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/update_profile', methods=['PATCH'])
        @jwt_required()
        @self.limiter.limit("10 per minute")
        def lectify_update_profile() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                            
                current_info_user = self.get_user(current_user)
                
                if not current_info_user:
                    return self.create_error_response("User not found", 404)
                
                data = request.get_json()

                update_fields = {}

                if "firstname" in data:
                    if data['firstname'].strip() == current_info_user['firstname']:
                        return self.create_error_response("Firstname is the same as the current one", 400)
                    
                    if not data['firstname'].strip():
                        return self.create_error_response("Firstname cannot be empty", 400)
                    
                    update_fields['firstname'] = data['firstname'].strip().capitalize()
                
                if "lastname" in data:
                    if data['lastname'].strip() == current_info_user['lastname']:
                        return self.create_error_response("Lastname is the same as the current one", 400)
                    
                    if not data['lastname'].strip():
                        return self.create_error_response("Lastname cannot be empty", 400)
                    
                    update_fields['lastname'] = data['lastname'].strip().capitalize()

                if "password" in data:
                    if not data['password'].strip():
                        return self.create_error_response("Password cannot be empty", 400)
                    
                    new_password = data['password'].strip()
                
                validation_error = validate_user_data({
                    "firstname": update_fields.get('firstname'),
                    "lastname": update_fields.get('lastname'),
                    "password": new_password if "password" in data else None
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)

                if "password" in data: 
                    update_fields['password'] = generate_password_hash(new_password)

                if not update_fields:
                    return self.create_error_response("No fields to update", 400)
                
                self.users_collection.update_one({"username": current_user}, {"$set": update_fields})
                
                return jsonify({"message": "Profile updated successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/update_image_profile', methods=['PUT'])
        @jwt_required()
        @self.limiter.limit("10 per minute")
        def lectify_update_image_profile() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                                
                current_info_user = self.get_user(current_user)
                
                if not current_info_user:
                    return self.create_error_response("User not found", 404)
                
                files = request.files.getlist('file')

                if len(files) > 1:
                    return self.create_error_response('Exactly one file must be uploaded', 400)

                if len(files) == 0 or not files[0]:
                    if not current_info_user['image_profile']:
                        return self.create_error_response('No profile image to remove', 400)

                    self.cloudinary.uploader.destroy(f'image_profile_{current_user}', resource_type="image")
                    self.users_collection.update_one({"username": current_user}, {"$set": {"image_profile": ""}})
                    return jsonify({'message': 'Profile image removed successfully'}), 200

                received_file = files[0]

                received_file.stream.seek(0, os.SEEK_END)
                file_size = received_file.stream.tell()
                received_file.stream.seek(0)

                if file_size > 5 * 1024 * 1024:
                    return self.create_error_response('File size exceeds the maximum limit of 5 MB.', 413)
                
                if not os.path.exists(self.output_path):
                    os.makedirs(self.output_path)

                filename_nosecure = received_file.filename
                filename_secure = secure_filename(filename_nosecure)

                file_extension = filename_secure.split('.')[-1].lower()
                self.filepath_secure = os.path.join(self.output_path, f'image_profile_{current_user}.{file_extension}')
                
                if file_extension not in self.valid_format_images:
                    return self.create_error_response(f'Invalid format. Supported formats: {", ".join(self.valid_formats_images)}', 400)
                
                for extensions in self.blocked_extensions:
                    if extensions in filename_secure:
                        return self.create_error_response(f'The filename seems suspicious and contains a blocked extension: {extensions}', 400)
                
                received_file.save(self.filepath_secure)

                mime_detector = magic.Magic(mime=True)
                expected_mime_type = self.expected_image_mime_types.get(file_extension)
                detected_mime_type = mime_detector.from_file(self.filepath_secure)

                if detected_mime_type != expected_mime_type:
                    return self.create_error_response(f'Invalid file type. Detected: {detected_mime_type}. Expected: {expected_mime_type}', 400)

                upload_result = self.cloudinary.uploader.upload(
                    self.filepath_secure,
                    public_id=f'image_profile_{current_user}',
                    overwrite=True, 
                    resource_type="image",
                    invalidate=True,
                    format='webp',
                    transformation=[
                        {"width": 500, "height": 500, "crop": "fill", "gravity": "center"},
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )

                image_url = upload_result.get('secure_url')
                
                if not image_url:
                    return self.create_error_response('Error uploading image to Cloudinary', 500)
                
                self.users_collection.update_one({"username": current_user}, {"$set": {"image_profile": image_url}})

                return jsonify({"message": "Profile image updated successfully", "image_profile": image_url}), 200
                
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

            finally:
                clean_up(
                    getattr(self, "filepath_secure", None),
                    getattr(self, "filepath_secure_webp", None),
                )

        @self.app.route('/lectify/ping_email_delete_account', methods=['POST'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_ping_email_delete_account() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                
                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                                
                current_info_user = self.get_user(current_user)
                
                if not current_info_user:
                    return self.create_error_response("User not found", 404)
                
                email = current_info_user['email']

                data = request.get_json()

                base_url = (data.get("base_url") or "").lower().strip()
                reset_password_page_url = (data.get("reset_password_page_url") or "").lower().strip()

                if not base_url or not reset_password_page_url:
                    return self.create_error_response("Base URL and Reset Password Page URL are required", 400)
                
                token = self.generate_hash()
                
                self.check_email_collection.update_one({
                    "email": email},
                    {
                        "$set": {
                            "type_verification": "delete_account",
                            "token": token,
                            "timestamp": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )

                link_verification = f"{base_url}/{reset_password_page_url}/{token}"

                SendEmailVerification().send_verification_email(email, link_verification, 'delete_account')

                return jsonify({"message": "Verification code sent to email",}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/pong_email_delete_account', methods=['DELETE'])
        @jwt_required()
        @self.limiter.limit("5 per minute")
        def lectify_pong_email_delete_account() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                
                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                                
                current_info_user = self.get_user(current_user)
                
                if not current_info_user:
                    return self.create_error_response("User not found", 404)
                
                email = current_info_user['email']
                
                data = request.get_json()

                token = (data.get("token") or "").strip()

                if not token:
                    return self.create_error_response("Token is required", 400)
                
                check_email_data = self.check_email_collection.find_one({"email": email})

                if not check_email_data:
                    return self.create_error_response("Email not found", 404)
                
                if check_email_data['type_verification'] != 'delete_account':
                    return self.create_error_response("Invalid verification type", 400)
                
                validation_error = validate_user_data({
                    "token": token
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                if check_email_data['token'] != token:
                    return self.create_error_response("Invalid verification token", 400)
                
                self.users_collection.delete_one({"username": current_user})
                self.check_email_collection.delete_one({"email": email})

                return jsonify({"message": "Account deleted successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/ping_email_reset_password', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_ping_check_email_reset_password() -> Response:
            try:                
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                
                data = request.get_json()

                email = (data.get("email") or "").lower().strip()
                base_url = (data.get("base_url") or "").lower().strip()
                reset_password_page_url = (data.get("reset_password_page_url") or "").lower().strip()

                if not email or not base_url or not reset_password_page_url:
                    return self.create_error_response("Email, Base URL and Reset Password Page URL are required", 400)
                
                if not self.get_email(email):
                    return self.create_error_response("Email not found", 404)
                
                token = self.generate_hash()
                
                self.check_email_collection.update_one({
                    "email": email},
                    {
                        "$set": {
                            "type_verification": "reset_password",
                            "token": token,
                            "timestamp": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )

                link_verification = f"{base_url}/{reset_password_page_url}/{email}/{token}"

                SendEmailVerification().send_verification_email(email, link_verification, 'reset_password')

                return jsonify({"message": "Verification sent to email",}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/pong_email_reset_password', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def lectify_pong_verify_email_reset_password() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)
                
                data = request.get_json()

                email = (data.get("email") or "").lower().strip()
                token = (data.get("token") or "").strip()
                new_password = (data.get("new_password") or "").strip()

                if not email or not token or not new_password:
                    return self.create_error_response("Email, Token, and new password are required", 400)
                
                validation_error = validate_user_data({
                    "email": email,
                    "token": token,
                    "password": new_password
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                check_email_data = self.check_email_collection.find_one({"email": email})

                if not check_email_data:
                    return self.create_error_response("Email not found", 404)
                
                if check_email_data['type_verification'] != 'reset_password':
                    return self.create_error_response("Invalid verification type", 400)
                
                if check_email_data['token'] != token:
                    return self.create_error_response("Invalid verification Token", 400)
                
                hashed_password = generate_password_hash(new_password)
                self.users_collection.update_one(
                    {"email": email},
                    {"$set": {"password": hashed_password}})

                self.check_email_collection.delete_one({"email": email})

                return jsonify({"message": "Password reset successfully"}), 200
            
            except Exception:
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/checkout', methods=['POST'])
        @jwt_required()
        @self.limiter.limit("10 per minute")
        def lectify_checkout() -> Response:
            try:
                current_user = self.user_or_ip()
                
                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block
                
                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                current_info_user = self.get_user(current_user)
                
                if not current_info_user:
                    return self.create_error_response("User account not found", 404)
                
                if not self.user_is_free(current_user):
                    return self.create_error_response("User already has a paid plan", 400)
            
                data = request.get_json()
                plan = data.get("plan", "").strip().lower()
                success_url = data.get("success_url" , "").strip()
                failure_url = data.get("failure_url", "").strip()
                pending_url = data.get("pending_url", "").strip()

                if not plan or plan not in self.plans:
                    return self.create_error_response("Plan is required", 400)
                
                if not success_url or not failure_url or not pending_url:
                    return self.create_error_response("Success, failure and pending URLs are required", 400)
                
                validation_error = validate_user_data({
                    "success_url": success_url,
                    "failure_url": failure_url,
                    "pending_url": pending_url
                })

                if validation_error:
                    return self.create_error_response(validation_error, 400)
                
                selected_plan = self.plans.get(plan)
                price = selected_plan['price']
                duration = selected_plan['duration']
                email = current_info_user['email']

                if not email:
                    return self.create_error_response("No email address found for this account", 404)

                preference_data = {
                    "items": [
                        {
                            "title": "Lectify Premium",
                            "quantity": 1,
                            "unit_price": price
                        }
                    ],
                    "payer": {
                        "email": email
                    },
                    "external_reference": f"{current_user}:{plan}",
                    "back_urls": {
                        "success": success_url,
                        "failure": failure_url,
                        "pending": pending_url
                    },
                    "auto_return": "approved"
                }

                preference_response = self.mercadopago_sdk.preference().create(preference_data)
                preference = preference_response["response"]
            
                return jsonify({'checkout_url': preference["init_point"]}), 200

            except Exception:
                return self.create_error_response('An error occurred while processing the request.', 500)

        @self.app.route('/lectify/webhook', methods=['POST'])
        def lectify_webhook() -> Response:
            try:
                data = request.get_json()
                payment_id = data["data"]["id"]
                payment_response = self.mercadopago_sdk.payment().get(payment_id)

                if payment_response["status"] != 200:
                    return self.create_error_response('Failed to retrieve payment information from Mercado Pago.', 400)

                payment = payment_response["response"]
                external_reference = payment["external_reference"]
                username, plan = external_reference.split(":")

                user = self.get_user(username)

                if user:
                    duration = self.plans[plan]["duration"]
                    now = datetime.now(timezone.utc)
                    end_date = now + duration

                    self.users_collection.update_one(
                        {"username": username},
                        {
                            "$set": {
                                "is_free": False,
                                "plan": plan,
                                "subscription_end": end_date
                            }
                        }
                    )
            
                return jsonify({'message': 'Webhook processed successfully.'}), 200

            except Exception:
                return self.create_error_response('An error occurred while processing the request.', 500)
                
    def run_production(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        self.app.run(debug=False, host=host, port=port, use_reloader=False)