from src.modules.vertex_ai import Vertex
from src.modules.extract_text import ExtractText
from src.modules.retention import Retention

from src.rabbitmq.publisher import publish_message, SUMMARIZE_QUEUE

from config.prompt_config import prompt_questions
from config.file_config import *
from config.limits_config import *
from limits import parse_many
from config.input_config import *

from config.providers.initialize_mongodb import initialize_mongodb
from config.providers.initialize_mercadopago import initialize_mercadopago, REVOKING_STATUSES
from config.providers.initialize_redis  import initialize_redis
from config.providers.initialize_cloudinary  import initialize_cloudinary

from src.utils.send_email_verification import SendEmailVerification
from src.utils.system_utils import clean_up, is_valid_email, validate_user_data, sanitize_filename, trim_source_text

from flask import Flask, request, jsonify, send_file, Response, g
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo.collection import Collection
from datetime import datetime, timezone,timedelta
from dotenv import load_dotenv
from decimal import Decimal
import cloudinary.uploader
from bson import ObjectId
import requests
import hashlib
import secrets
import string
import random
import magic
import json
import math
import uuid
import hmac
import os
import re

load_dotenv()

class Server:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)

        self.app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        self.app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        self.app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

        self.jwt: JWTManager = JWTManager(self.app)

        mongo = initialize_mongodb()
        mercadopago = initialize_mercadopago()
        redis = initialize_redis(self.app, self.user_or_ip)
        self.cloudinary = initialize_cloudinary() 

        self.grid_fs = mongo["grid_fs"]
        self.documents_collection = mongo["documents_collection"]
        self.questions_collection: Collection = mongo["questions_collection"]
        self.check_email_collection: Collection = mongo["check_email_collection"]
        self.users_collection: Collection = mongo["users_collection"]
        self.check_summarize_collection: Collection = mongo["check_summarize_collection"]
        self.transactions_collection: Collection = mongo["transactions_collection"]
        
        self.mercadopago_sdk = mercadopago["mercadopago"]
        self.mercadopago_webhook_secret = mercadopago["webhook_secret"]
        self.plans = mercadopago['plans']

        self.retention = Retention(
            mongo["grid_fs"],
            mongo["documents_collection"],
            mongo["chunks_collection"],
            mongo["questions_collection"]
        )

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

        self.youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/)?[a-zA-Z0-9_-]{11}')
        self.max_url_length: int = 200

        self._register_routes()
        
    def create_error_response(self, message: str, code: int) -> Response:
        return jsonify({'error': message}), code

    def get_user(self, username) -> dict | None:
        return self.users_collection.find_one({"username": username})
    
    def get_email(self, email) -> dict | None:
        return self.users_collection.find_one({"email": email})

    def delete_user_documents(self, username: str) -> int:
        documents = self.documents_collection.find({"username": username}, {"_id": 1})

        removed = 0

        for document in documents:
            self.retention.delete_document(document["_id"])
            removed += 1

        self.questions_collection.delete_many({"username": username})

        return removed

    def summary_text(self, grid_out) -> str:
        filetype = getattr(grid_out, "filetype", "md")

        os.makedirs(self.output_path, exist_ok=True)
        g.filepath_secure = os.path.join(self.output_path, f"{secrets.token_hex(8)}.{filetype}")

        with open(g.filepath_secure, 'wb') as file:
            file.write(grid_out.read())

        if filetype == 'pdf':
            return ExtractText().extract_text_pdf(g.filepath_secure).get('data') or ''

        return ExtractText().extract_text_markdown(g.filepath_secure).get('data') or ''

    def parse_questions_json(self, raw: str) -> dict:
        text = (raw or '').strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return json.loads(text)

    def questions_source_from_upload(self, username: str) -> tuple:
        files = request.files.getlist('file')

        if len(files) != 1:
            return None, self.create_error_response('Exactly one file must be uploaded', 400)

        received_file = files[0]

        if not received_file.filename:
            return None, self.create_error_response('No files received', 400)

        file_size_bytes = len(received_file.read())
        received_file.seek(0)

        if (file_size_bytes / 1024) / 1024 > 5:
            return None, self.create_error_response('File size exceeds the maximum limit of 5 MB.', 413)

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        filename_secure = secure_filename(received_file.filename)
        g.filepath_secure = os.path.join(self.output_path, f"{secrets.token_hex(8)}_{filename_secure}")

        if len(filename_secure) > 200:
            return None, self.create_error_response('File name exceeds the maximum length of 200 characters.', 400)

        file_extension = g.filepath_secure.split('.')[-1].lower()

        if file_extension not in self.valid_formats:
            return None, self.create_error_response(f'Invalid format. Supported formats: {", ".join(self.valid_formats)}', 400)

        for extensions in self.blocked_extensions:
            if extensions in filename_secure:
                return None, self.create_error_response(f'The filename seems suspicious and contains a blocked extension: {extensions}', 400)

        received_file.save(g.filepath_secure)

        mime_detector = magic.Magic(mime=True)
        expected_mime_type = self.expected_mime_types.get(file_extension)
        detected_mime_type = mime_detector.from_file(g.filepath_secure)

        if expected_mime_type == 'text/markdown':
            detected_mime_type = expected_mime_type

        if detected_mime_type != expected_mime_type:
            return None, self.create_error_response(f'Invalid file type. Detected: {detected_mime_type}. Expected: {expected_mime_type}', 400)

        label = 'Markdown' if file_extension == 'md' else 'PDF'

        try:
            if file_extension == 'md':
                extracted = ExtractText().extract_text_markdown(g.filepath_secure)

            else:
                extracted = ExtractText().extract_text_pdf(g.filepath_secure)

        except Exception:
            self.app.logger.exception(f'Error during extraction of {label} text')
            return None, self.create_error_response(f'Error during extraction of {label} text', 400)

        source_text = trim_source_text(extracted.get('data') or '', MAX_SOURCE_TEXT_CHARS)

        if not source_text.strip():
            suffix = 'Markdown file' if file_extension == 'md' else 'PDF'
            return None, self.create_error_response(f'No extractable text found in the {suffix}', 400)

        return (source_text.strip(), None, self.retention.expires_at(), filename_secure), None

    def questions_source_from_summary(self, username: str, file_id: str) -> tuple:
        try:
            object_id = ObjectId(file_id)

        except Exception:
            return None, self.create_error_response('Invalid file id', 400)

        document = self.documents_collection.find_one({"_id": object_id, "username": username})

        if not document:
            return None, self.create_error_response('Document not found in the database', 404)

        grid_out = self.grid_fs.get(object_id)
        source_text = trim_source_text(self.summary_text(grid_out), MAX_SOURCE_TEXT_CHARS).strip()

        if not source_text:
            return None, self.create_error_response('No extractable text found in the summary', 400)

        return (source_text, object_id, document.get("expires_at"), grid_out.filename), None
    
    def generate_code(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)).strip()

    def generate_hash(self) -> str:
        return secrets.token_hex(32)
    
    def is_email_verified(self, email) -> bool:
        return self.check_email_collection.find_one({
            "email": email,
            "is_verified": True}) is not None
    
    def user_is_free(self, uid: str) -> bool:
        current_user = self.get_user(uid)

        if not current_user:
            return True

        subscription_end = current_user.get("subscription_end")
        has_active_subscription = False

        if isinstance(subscription_end, datetime):
            if subscription_end.tzinfo is None:
                subscription_end = subscription_end.replace(tzinfo=timezone.utc)
                
            has_active_subscription = datetime.now(timezone.utc) < subscription_end

        if has_active_subscription:
            if current_user.get("is_free", True):
                self.users_collection.update_one(
                    {"username": uid},
                    {"$set": {"is_free": False}}
                )
            return False

        if not current_user.get("is_free", True):
            self.users_collection.update_one(
                {"username": uid},
                {"$set": {"is_free": True}}
            )

        return True
    
    def current_identity(self) -> str | None:
        try:
            verify_jwt_in_request(optional=True)

            return get_jwt_identity()

        except Exception:
            return None

    def rate_limit_key(self) -> str:
        for refresh in (False, True):
            try:
                verify_jwt_in_request(refresh=refresh, optional=not refresh)
                identity = get_jwt_identity()

                if identity:
                    return identity

            except Exception:
                continue

        return get_remote_address()
        
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
                
                return None

    def check_and_apply_block(self, current_user: str | None, increment: bool = True) -> Response | None:
        if not current_user:
            return None

        block_key = f"blocked:{current_user}"
        count_key = f"count429:{current_user}"

        ttl = self.redis_client.ttl(block_key)
        if ttl > 0:
            minutes = max(1, math.ceil(ttl / 60))
            return self.create_error_response(f"You have been temporarily blocked due to repeated rate limit violations. Please try again in {minutes} minute(s).", 403)

        count =  None

        if increment:
            count = self.redis_client.incr(count_key)

            if count == 1:
                self.redis_client.expire(count_key, 300)

        if increment and count == 3:
            return self.create_error_response("You are approaching the rate limit. One more failed attempt will block you for 30 minutes. Please try again later.", 429)

        if increment and count >= 4:
            self.redis_client.set(block_key, 1, ex=1800)
            self.redis_client.delete(count_key)
            
            return self.create_error_response("You have been temporarily blocked due to repeated rate limit violations.", 403)
        
        return None

    def plan_limit_string(self, plan: str | None, endpoint: str | None) -> str:
        quota = PLAN_LIMITS.get(plan)

        if not quota:
            return ABUSE_LIMIT

        rate = ENDPOINT_RATE_LIMITS.get(endpoint)

        return f'{rate};{quota}' if rate else quota

    def get_dynamic_limit(self) -> str:
        current_user = self.current_identity()

        if not current_user or self.user_is_free(current_user):
            return ABUSE_LIMIT

        user_info = self.get_user(current_user) or {}

        return self.plan_limit_string(user_info.get("plan"), request.endpoint)

    QUOTA_FEATURES = {
        "summarize": "lectify_summarize",
        "questions": "lectify_questions"
    }

    READ_ENDPOINTS = frozenset({
        "health_check",
        "lectify_profile",
        "lectify_usage",
        "lectify_check_summarize",
        "lectify_summarize_files",
        "lectify_summarize_files_by_id",
        "lectify_questions_list",
        "lectify_questions_by_id"
    })

    def describe_period(self, item) -> tuple[str, int]:
        """Nome amigavel do periodo de um limite e sua duracao em segundos."""
        granularity = getattr(getattr(item, "GRANULARITY", None), "name", "")
        multiples = getattr(item, "multiples", 1) or 1

        if granularity == "day" and multiples % 7 == 0:
            return "week", item.get_expiry()

        if granularity == "month":
            return "month", item.get_expiry()

        return granularity or "period", item.get_expiry()

    def usage_for(self, uid: str, endpoint: str, limit_string: str) -> list[dict]:
        entries = []

        for item in parse_many(limit_string):
            stats = self.limiter.limiter.get_window_stats(item, uid, endpoint)
            period, seconds = self.describe_period(item)

            entries.append({
                "period": period,
                "period_seconds": seconds,
                "limit": item.amount,
                "remaining": stats.remaining,
                "used": max(item.amount - stats.remaining, 0),
                "reset_at": datetime.fromtimestamp(stats.reset_time, timezone.utc).isoformat()
            })

        return entries

    def breached_quota_period(self, breached) -> str | None:
        limit = getattr(breached, "limit", None)

        if limit is None:
            return None

        granularity = getattr(getattr(limit, "GRANULARITY", None), "name", "")
        multiples = getattr(limit, "multiples", 1) or 1

        if granularity == "month":
            return "Monthly"

        if granularity == "day" and multiples % 7 == 0:
            return "Weekly"

        return None

    def rebuild_subscription(self, uid: str) -> tuple[str | None, datetime | None]:
        transactions = self.transactions_collection.find(
            {"uid": uid, "status": "approved"}
        ).sort("approved_at", 1)

        plan = None
        subscription_end = None

        for transaction in transactions:
            transaction_plan = transaction.get("plan")
            approved_at = transaction.get("approved_at")

            if transaction_plan not in self.plans or not isinstance(approved_at, datetime):
                continue

            if approved_at.tzinfo is None:
                approved_at = approved_at.replace(tzinfo=timezone.utc)

            subscription_is_active = bool(subscription_end and subscription_end > approved_at)
            subscription_start = subscription_end if subscription_is_active else approved_at
            subscription_end = subscription_start + timedelta(days=self.plans[transaction_plan]["days"])

            current_plan = plan if subscription_is_active else None

            if not (current_plan and PLAN_RANKS.get(current_plan, 0) > PLAN_RANKS.get(transaction_plan, 0)):
                plan = transaction_plan

        return plan, subscription_end

    def verify_mercadopago_signature(self, payment_id: str) -> bool:
        if not self.mercadopago_webhook_secret:
            self.app.logger.warning(
                "MERCADOPAGO_WEBHOOK_SECRET is not set: webhook signatures are not being verified."
            )
            return True

        signature = request.headers.get("x-signature", "")
        request_id = request.headers.get("x-request-id", "")

        parts = dict(
            piece.split("=", 1) for piece in signature.split(",") if "=" in piece
        )

        ts = parts.get("ts", "").strip()
        received_signature = parts.get("v1", "").strip()

        if not ts or not received_signature:
            return False

        data_id = str(payment_id)

        if data_id.isalnum():
            data_id = data_id.lower()

        manifest = f"id:{data_id};"

        if request_id:
            manifest += f"request-id:{request_id};"

        manifest += f"ts:{ts};"

        expected_signature = hmac.new(
            self.mercadopago_webhook_secret.encode("utf-8"),
            manifest.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, received_signature)

    def _register_routes(self) -> None:
        @self.app.errorhandler(429)
        def ratelimit_error(e) -> Response:
            breached = getattr(self.limiter, "current_limit", None)

            quota_features = {
                "lectify_summarize": "lectify summarize",
                "lectify_questions": "lectify questions"
            }

            feature = quota_features.get(request.endpoint)
            period = self.breached_quota_period(breached)

            if feature and period:
                return self.create_error_response(f"{period} {feature} quota reached for your plan. Upgrade your plan to continue using this feature.", 429)

            current_user = self.current_identity()

            response_check_and_apply_block = self.check_and_apply_block(
                current_user,
                increment=request.endpoint not in self.READ_ENDPOINTS
            )

            if response_check_and_apply_block:
                return response_check_and_apply_block

            return self.create_error_response("Too many requests. Please try again later.", 429)
        
        @self.app.after_request
        def after_request(response) -> Response:
            endpoint = request.endpoint
            if endpoint in ('lectify_questions', 'lectify_update_image_profile'):
                clean_up(g.get("filepath_secure"))
            
            return response
        
        @self.app.route('/health', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def health_check():
            return jsonify({"status": "healthy"}), 200

        @self.app.route('/lectify/summarize', methods=['POST'])
        @self.limiter.limit(ABUSE_LIMIT, scope="abuse")
        @self.limiter.limit(self.get_dynamic_limit, deduct_when=lambda response: response.status_code == 201)
        @jwt_required()
        def lectify_summarize() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if self.user_is_free(current_user):
                    return self.create_error_response("Upgrade your plan to continue using this feature.", 403)
                            
                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

                data = request.get_json()

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)
                
                missing_fields = [field for field in self.required_fields if field not in data]
                if missing_fields:
                    missing_fields_str = ', '.join(missing_fields)
                    return self.create_error_response(f"Missing required fields: {missing_fields_str}", 400)
                
                youtube_url = data.get('youtube_url')
                output_format = data.get('output_format')
                language_select = data.get('language_select')
                
                if not isinstance(youtube_url, str):
                    return {"error": "Youtube Url client must be a string"}, 400

                if not isinstance(output_format, str):
                    return {"error": "Output Format Url client must be a string"}, 400

                if not isinstance(language_select, str):
                    return {"error": "Language Select client must be a string"}, 400

                if not youtube_url:
                    return self.create_error_response('Missing YouTube URL', 400)

                if not output_format:
                    return self.create_error_response('Missing output format', 400)

                if not language_select:
                    return self.create_error_response('Missing language selection', 400)
                
                if len(youtube_url) > self.max_url_length:
                    return self.create_error_response(f'URL exceeds maximum length of {self.max_url_length} characters', 400)

                if not youtube_url.startswith("https://"):
                    youtube_url = "https://" + youtube_url

                if not re.match(self.youtube_regex, youtube_url):
                    return self.create_error_response('Invalid YouTube URL', 400)
                
                if output_format not in self.valid_formats:
                    return self.create_error_response(f"Invalid format. Supported formats: {', '.join(self.valid_formats)}", 400)
                
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
                        queue=SUMMARIZE_QUEUE,
                        message={
                            'youtube_url': youtube_url,
                            'language_select': language_select,
                            'output_format': output_format,
                            'username': current_user
                        },
                        priority=PLAN_RANKS.get((self.get_user(current_user) or {}).get("plan"), 1)
                    )

                    return jsonify({"message": "Your request has been successfully placed in the RabbitMQ queue and will be processed shortly"}), 201

                except Exception:
                    self.app.logger.exception('Error during publishing message to queue in summarize')
                    return self.create_error_response('Error during publishing message to queue in summarize', 500)
                
            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/check_summarize', methods=['POST'])
        @self.limiter.limit("50 per minute")
        @jwt_required()
        def lectify_check_summarize() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if self.user_is_free(current_user):
                    return self.create_error_response("Upgrade your plan to continue using this feature.", 403)

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)
                
                data = request.get_json()
                
                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)
                
                missing_fields = [field for field in self.required_fields if field not in data]
                if missing_fields:
                    missing_fields_str = ', '.join(missing_fields)
                    return self.create_error_response(f"Missing required fields: {missing_fields_str}", 400)

                youtube_url = data.get('youtube_url')
                output_format = data.get('output_format')
                language_select = data.get('language_select')

                if not isinstance(youtube_url, str):
                    return {"error": "Language Select client must be a string"}, 400

                if not isinstance(output_format, str):
                    return {"error": "Language Select client must be a string"}, 400

                if not isinstance(language_select, str):
                    return {"error": "Language Select client must be a string"}, 400

                if not youtube_url:
                    return self.create_error_response('Missing YouTube URL', 400)

                if not output_format:
                    return self.create_error_response('Missing output format', 400)

                if not language_select:
                    return self.create_error_response('Missing language selection', 400)
                
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
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/summarize/files', methods=['GET'])
        @self.limiter.limit("30 per minute")
        @jwt_required()
        def lectify_summarize_files() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

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
                            "expires_at": getattr(grid_out, "expires_at", None),
                            "source": getattr(grid_out, "source", None),
                        })

                    return jsonify(files), 200

                except Exception:
                    self.app.logger.exception('Error during fetching documents from the database')
                    return self.create_error_response('Error during fetching documents from the database', 400)

            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

                    
        @self.app.route('/lectify/summarize/files/<string:file_id>', methods=['GET'])
        @self.limiter.limit("20 per minute")
        @jwt_required()
        def lectify_summarize_files_by_id(file_id: str) -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

                try:
                    file_documents_collection = self.documents_collection.find_one({
                        "_id": ObjectId(file_id),
                        "username": current_user
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
                    self.app.logger.exception('Error during fetching document from the database')
                    return self.create_error_response('Error during fetching document from the database', 400)
            
            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/summarize/files/<string:file_id>', methods=['DELETE'])
        @self.limiter.limit("10 per minute")
        @jwt_required()
        def lectify_summarize_files_delete(file_id: str) -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

                try:
                    object_id = ObjectId(file_id)

                except Exception:
                    return self.create_error_response('Invalid file id', 400)

                file_documents_collection = self.documents_collection.find_one({
                    "_id": object_id,
                    "username": current_user
                })

                if not file_documents_collection:
                    return self.create_error_response('Document not found in the database', 404)

                removed_questions = self.retention.delete_document(object_id)

                return jsonify({
                    "message": "Document deleted successfully",
                    "removed_questions": removed_questions
                }), 200

            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/questions', methods=['GET'])
        @self.limiter.limit("30 per minute")
        @jwt_required()
        def lectify_questions_list() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

                quizzes = self.questions_collection.find(
                    {"username": current_user},
                    {"questions": 0, "source_hash": 0}
                ).sort("created_at", -1)

                return jsonify([
                    {
                        "id": str(quiz["_id"]),
                        "title": quiz.get("title"),
                        "file_id": str(quiz["file_id"]) if quiz.get("file_id") else None,
                        "created_at": quiz.get("created_at"),
                        "expires_at": quiz.get("expires_at")
                    }
                    for quiz in quizzes
                ]), 200

            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/questions/<string:question_id>', methods=['GET'])
        @self.limiter.limit("30 per minute")
        @jwt_required()
        def lectify_questions_by_id(question_id: str) -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

                try:
                    object_id = ObjectId(question_id)

                except Exception:
                    return self.create_error_response('Invalid question id', 400)

                quiz = self.questions_collection.find_one({
                    "_id": object_id,
                    "username": current_user
                })

                if not quiz:
                    return self.create_error_response('Questions not found in the database', 404)

                return jsonify({
                    "id": str(quiz["_id"]),
                    "title": quiz.get("title"),
                    "file_id": str(quiz["file_id"]) if quiz.get("file_id") else None,
                    "created_at": quiz.get("created_at"),
                    "expires_at": quiz.get("expires_at"),
                    "questions": quiz.get("questions")
                }), 200

            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/questions', methods=['POST'])
        @self.limiter.limit(ABUSE_LIMIT, scope="abuse")
        @self.limiter.limit(self.get_dynamic_limit, deduct_when=lambda response: response.status_code == 201)
        @jwt_required()
        def lectify_questions() -> Response:
            try:
                current_user = self.user_or_ip()

                response_check_and_apply_block = self.check_and_apply_block(current_user, increment=False)
                if response_check_and_apply_block:
                    return response_check_and_apply_block

                if self.user_is_free(current_user):
                    return self.create_error_response("Upgrade your plan to continue using this feature.", 403)

                if not current_user:
                    return self.create_error_response("You are not authorized to access this resource", 401)

                if not self.get_user(current_user):
                    return self.create_error_response("User not found", 404)

                file_id = request.form.get('file_id') or (request.get_json(silent=True) or {}).get('file_id')

                if file_id:
                    source, error = self.questions_source_from_summary(current_user, file_id)

                else:
                    source, error = self.questions_source_from_upload(current_user)

                if error:
                    return error

                source_text, linked_file_id, expires_at, title = source
                source_hash = hashlib.sha256(source_text.encode('utf-8')).hexdigest()

                stored_questions = self.questions_collection.find_one({
                    "username": current_user,
                    "source_hash": source_hash
                })

                if stored_questions:
                    if linked_file_id and not stored_questions.get("file_id"):
                        self.questions_collection.update_one(
                            {"_id": stored_questions["_id"]},
                            {"$set": {"file_id": linked_file_id, "expires_at": expires_at}}
                        )

                    return jsonify(stored_questions["questions"]), 200

                try:
                    response_generative_ai = Vertex().start_chat(f'{prompt_questions}{source_text}')
                    response_generative_ai_json = self.parse_questions_json(response_generative_ai['data'])

                except Exception:
                    self.app.logger.exception("Error during chat generation")
                    return self.create_error_response("Error during chat generation", 400)

                self.questions_collection.update_one(
                    {"username": current_user, "source_hash": source_hash},
                    {
                        "$set": {
                            "file_id": linked_file_id,
                            "title": title,
                            "questions": response_generative_ai_json,
                            "created_at": datetime.now(timezone.utc),
                            "expires_at": expires_at
                        }
                    },
                    upsert=True
                )

                return jsonify(response_generative_ai_json), 201

            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                email = data.get("email")
                
                if not isinstance(email, str):
                    return self.create_error_response("Email must be a string", 400)

                if not email:
                    return self.create_error_response("Email is required", 400)
                
                email = email.strip().lower()

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
                self.app.logger.exception('An error occurred while processing the request')
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                email = data.get("email")
                code = data.get("code")

                if not isinstance(email, str):
                    return {"error": "Email must be a string"}, 400

                if not isinstance(code, str):
                    return {"error": "Code must be a string"}, 400

                if not email or not code:
                    return self.create_error_response("Email and code are required", 400)

                email = email.strip().lower()
                code = code.strip().lower()
                
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
                self.app.logger.exception('An error occurred while processing the request')
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                username = data.get("username")
                password = data.get("password")
                email = data.get("email")
                firstname = data.get("firstname")
                lastname = data.get("lastname")

                fields = {
                    "username": username,
                    "password": password,
                    "email": email,
                    "firstname": firstname,
                    "lastname": lastname
                }

                for field, value in fields.items():
                    if not isinstance(value, str):
                        return self.create_error_response(f"{field} must be a string", 400)
                
                username = fields["username"].strip().lower()
                password = fields["password"].strip()
                email = fields["email"].strip().lower()
                firstname = fields["firstname"].strip().capitalize()
                lastname = fields["lastname"].strip().capitalize()

                if not username or not password or not email or not firstname or not lastname:
                    return self.create_error_response("Username, password, email, firstname and lastname are required", 400)
                
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
                self.app.logger.exception('An error occurred while processing the request')
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                username = data.get("username")
                email = data.get("email")
                password = data.get("password")

                if username and not isinstance(username, str):
                    return self.create_error_response("Username must be a string", 400)

                if email and not isinstance(email, str):
                    return self.create_error_response("Email must be a string", 400)

                if password and not isinstance(password, str):
                    return self.create_error_response("Password must be a string", 400)

                username = (username or "").strip().lower()
                email = (email or "").strip().lower()
                password = (password or "").strip()

                if not username and not email:
                    return self.create_error_response("You must provide either a username or an email", 400)

                if not password:
                    return self.create_error_response("Password is required", 400)

                if email and not is_valid_email(email):
                    return self.create_error_response("Invalid email format", 400)
                
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
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/profile', methods=['GET'])
        @self.limiter.limit("50 per minute")
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
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/usage', methods=['GET'])
        @self.limiter.limit("30 per minute")
        @jwt_required()
        def lectify_usage() -> Response:
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

                if self.user_is_free(current_user):
                    return jsonify({"is_free": True, "plan": None, "features": {}}), 200

                plan = current_info_user.get("plan")
                features = {
                    name: self.usage_for(current_user, endpoint, self.plan_limit_string(plan, endpoint))
                    for name, endpoint in self.QUOTA_FEATURES.items()
                }

                return jsonify({
                    "is_free": False,
                    "plan": plan,
                    "features": features
                }), 200

            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/refresh_token', methods=['POST'])
        @self.limiter.limit("5 per minute")
        @jwt_required(refresh=True)
        def lectify_refresh_token() -> Response:
            try:                
                current_user = get_jwt_identity()
                
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
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/update_profile', methods=['PATCH'])
        @self.limiter.limit("10 per minute")
        @jwt_required()
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                if "firstname" in data:
                    if not isinstance(data["firstname"], str):
                        return {"error": "Firstname must be a string"}, 400

                if "lastname" in data:
                    if not isinstance(data["lastname"], str):
                        return {"error": "Lastname must be a string"}, 400

                if "password" in data:
                    if not isinstance(data["password"], str):
                        return {"error": "Password must be a string"}, 400

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
                
                result = self.users_collection.update_one({"username": current_user}, {"$set": update_fields})

                if result.matched_count == 0:
                    return self.create_error_response("Client not found", 404)
                
                return jsonify({
                    "message": "Profile updated successfully",
                    "updated_fields": list(update_fields.keys()),
                    "modified": result.modified_count > 0
                }), 200
            
            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/update_image_profile', methods=['PUT'])
        @self.limiter.limit("10 per minute")
        @jwt_required()
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

                if not received_file.filename:
                    return self.create_error_response('No files received', 400)

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
                g.filepath_secure = os.path.join(self.output_path, f'image_profile_{current_user}_{secrets.token_hex(8)}.{file_extension}')
                
                if file_extension not in self.valid_format_images:
                    return self.create_error_response(f'Invalid format. Supported formats: {", ".join(self.valid_format_images)}', 400)
                
                for extensions in self.blocked_extensions:
                    if extensions in filename_secure:
                        return self.create_error_response(f'The filename seems suspicious and contains a blocked extension: {extensions}', 400)
                
                received_file.save(g.filepath_secure)

                mime_detector = magic.Magic(mime=True)
                expected_mime_type = self.expected_image_mime_types.get(file_extension)
                detected_mime_type = mime_detector.from_file(g.filepath_secure)

                if detected_mime_type != expected_mime_type:
                    return self.create_error_response(f'Invalid file type. Detected: {detected_mime_type}. Expected: {expected_mime_type}', 400)

                upload_result = self.cloudinary.uploader.upload(
                    g.filepath_secure,
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
                
                result = self.users_collection.update_one({"username": current_user}, {"$set": {"image_profile": image_url}})

                if not result.modified_count:
                    return self.create_error_response('Error updating user profile image', 500)

                return jsonify({"message": "Profile image updated successfully", "image_profile": image_url}), 200
                
            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

            finally:
                clean_up(g.get("filepath_secure"))

        @self.app.route('/lectify/ping_email_delete_account', methods=['POST'])
        @self.limiter.limit("5 per minute")
        @jwt_required()
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

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
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)
        
        @self.app.route('/lectify/pong_email_delete_account', methods=['DELETE'])
        @self.limiter.limit("5 per minute")
        @jwt_required()
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                token = data.get("token")

                if not isinstance(token, str):
                    return {"error": "Token must be a string"}, 400

                if not token:
                    return self.create_error_response("Token is required", 400)

                token = token.strip()
                
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
                
                self.delete_user_documents(current_user)
                self.check_summarize_collection.delete_one({"username": current_user})
                self.users_collection.delete_one({"username": current_user})
                self.check_email_collection.delete_one({"email": email})

                return jsonify({"message": "Account deleted successfully"}), 200
            
            except Exception:
                self.app.logger.exception('An error occurred while processing the request')
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                email = data.get("email")
                base_url = data.get("base_url")
                reset_password_page_url = data.get("reset_password_page_url")

                if not isinstance(email, str):
                    return self.create_error_response("Email must be a string", 400)

                if not isinstance(base_url, str):
                    return self.create_error_response("Base Url must be a string", 400)

                if not isinstance(reset_password_page_url, str):
                    return self.create_error_response("Reset Password Page Url must be a string", 400)

                email = email.strip().lower()
                base_url = base_url.strip().lower()
                reset_password_page_url = reset_password_page_url.strip().lower()

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
                self.app.logger.exception('An error occurred while processing the request')
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

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                email = data.get("email")
                token = data.get("token")
                new_password = data.get("new_password")

                if not isinstance(email, str):
                    return self.create_error_response("Email must be a string", 400)

                if not isinstance(token, str):
                    return self.create_error_response("Token must be a string", 400)

                if not isinstance(new_password, str):
                    return self.create_error_response("New Password must be a string", 400)

                email = email.strip().lower()
                token = token.strip()
                new_password = new_password.strip()

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
                self.app.logger.exception('An error occurred while processing the request')
                return self.create_error_response('An error occurred while processing the request', 500)

        @self.app.route('/lectify/checkout', methods=['POST'])
        @self.limiter.limit("10 per minute")
        @jwt_required()
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
                    return self.create_error_response("User not found", 404)
                
                data = request.get_json()

                if not isinstance(data, dict):
                    return self.create_error_response("Request body must be a JSON object", 400)

                if not data:
                    return self.create_error_response('No data provided', 400)

                unknown_fields = set(data.keys()) - ALLOWED_FIELDS

                if unknown_fields:
                    return self.create_error_response(f"Disallowed fields found: {', '.join(unknown_fields)}", 400)

                plan = data.get("plan")
                success_url = data.get("success_url")
                failure_url = data.get("failure_url")
                pending_url = data.get("pending_url")

                fields = {
                    "plan": plan,
                    "success_url": success_url,
                    "failure_url": failure_url,
                    "pending_url": pending_url
                }

                for field, value in fields.items():
                    if not isinstance(value, str):
                        return self.create_error_response(
                            f"{field} must be a string", 400)

                plan = fields["plan"].strip().lower()
                success_url = fields["success_url"].strip()
                failure_url = fields["failure_url"].strip()
                pending_url = fields["pending_url"].strip()

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
                email = current_info_user['email']

                if not email:
                    return self.create_error_response("No email address found for this account", 404)

                transaction_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)
                
                self.transactions_collection.insert_one({
                    "transaction_id": transaction_id,
                    "uid": current_user,
                    "plan": plan,
                    "amount": price,
                    "status": "pending",
                    "mercadopago_payment_id": None,
                    "created_at": now,
                    "expires_at": now + timedelta(days=30)
                })

                preference_data = {
                    "items": [
                        {
                            "title": "Lectify Premium",
                            "quantity": 1,
                            "unit_price": price,
                            "currency_id": "BRL"
                        }
                    ],
                    "payer": {
                        "email": email
                    },
                    "external_reference": f"{current_user}:{plan}:{transaction_id}",
                    "back_urls": {
                        "success": success_url,
                        "failure": failure_url,
                        "pending": pending_url
                    },
                    "auto_return": "approved"
                }

                preference_response = self.mercadopago_sdk.preference().create(preference_data)
                preference = preference_response["response"]

                self.transactions_collection.update_one(
                    {"transaction_id": transaction_id},
                    {
                        "$set": {
                            "preference_id": str(preference["id"]),
                            "checkout_url": preference["init_point"]
                        }
                    }
                )
            
                return jsonify({'checkout_url': preference["init_point"]}), 200

            except Exception:
                self.app.logger.exception('An error occurred while processing the request.')
                return self.create_error_response('An error occurred while processing the request.', 500)

        @self.app.route('/lectify/webhook', methods=['POST'])
        def lectify_webhook() -> Response:
            try:
                data = request.get_json(silent=True) or {}

                payment_id = (
                    data.get("data", {}).get("id")
                    or request.args.get("data.id")
                )

                if not payment_id:
                    return self.create_error_response("Payment ID not found", 400)

                if not self.verify_mercadopago_signature(payment_id):
                    return self.create_error_response("Invalid webhook signature", 401)

                payment_response = self.mercadopago_sdk.payment().get(payment_id)

                if payment_response["status"] != 200:
                    return self.create_error_response('Failed to retrieve payment information from Mercado Pago.', 400)

                payment = payment_response["response"]
                status = payment.get("status")

                external_reference = payment.get("external_reference")

                if not external_reference:
                    return self.create_error_response("External reference not found", 400)
                
                parts = external_reference.split(":")

                if len(parts) != 3:
                    return self.create_error_response("Invalid external reference", 400)

                uid, plan, transaction_id = parts

                if plan not in self.plans:
                    return self.create_error_response("Invalid plan", 400)

                transaction = self.transactions_collection.find_one({"transaction_id": transaction_id})

                if not transaction:
                    return self.create_error_response("Transaction not found", 404)

                if transaction.get("uid") != uid or transaction.get("plan") != plan:
                    return self.create_error_response("Transaction does not match the payment", 400)

                if status in REVOKING_STATUSES:
                    if transaction.get("status") in REVOKING_STATUSES:
                        return jsonify({"message": "Reversal already processed", "status": transaction.get("status")}), 200

                    self.transactions_collection.update_one(
                        {"transaction_id": transaction_id},
                        {
                            "$set": {
                                "status": status,
                                "refunded_at": datetime.now(timezone.utc),
                                "mercadopago_payment_id": str(payment_id)
                            }
                        }
                    )

                    refunded_user = self.get_user(uid)

                    if not refunded_user:
                        return self.create_error_response("User not found", 404)

                    now = datetime.now(timezone.utc)
                    remaining_plan, subscription_end = self.rebuild_subscription(uid)

                    still_active = bool(subscription_end and subscription_end > now)

                    update_user = {
                        "$set": {
                            "is_free": not still_active,
                            "plan": remaining_plan if still_active else None,
                            "subscription_end": subscription_end if still_active else None
                        }
                    }

                    if refunded_user.get("mercadopago_payment_id") == str(payment_id):
                        update_user["$unset"] = {"mercadopago_payment_id": ""}

                    self.users_collection.update_one({"username": uid}, update_user)

                    return jsonify({
                        "message": "Payment reversed and period revoked" if still_active else "Payment reversed and plan revoked",
                        "status": status,
                        "subscription_end": subscription_end.isoformat() if still_active else None
                    }), 200

                if status != "approved":
                    return jsonify({
                        "message": "Payment not approved",
                        "status": status
                    }), 200

                if transaction.get("status") == "approved":
                    return jsonify({"message": "Payment already processed"}), 200

                current_info_user = self.get_user(uid)

                if not current_info_user:
                    return self.create_error_response("User not found", 404)

                expected_price = Decimal(str(self.plans[plan]["price"]))
                paid_price = Decimal(str(payment.get("transaction_amount")))

                if paid_price != expected_price:
                    return self.create_error_response("Payment amount does not match the plan price", 400)

                selected_plan = self.plans[plan]

                now = datetime.now(timezone.utc)
                current_subscription_end = current_info_user.get("subscription_end")

                if isinstance(current_subscription_end, datetime):
                    if current_subscription_end.tzinfo is None:
                        current_subscription_end = current_subscription_end.replace(tzinfo=timezone.utc)
                else:
                    current_subscription_end = None

                subscription_is_active = bool(current_subscription_end and current_subscription_end > now)

                subscription_start = current_subscription_end if subscription_is_active else now
                subscription_end = subscription_start + timedelta(days=selected_plan["days"])

                current_plan = current_info_user.get("plan") if subscription_is_active else None
                effective_plan = plan

                if current_plan and PLAN_RANKS.get(current_plan, 0) > PLAN_RANKS.get(plan, 0):
                    effective_plan = current_plan

                self.transactions_collection.update_one(
                    {"transaction_id": transaction_id},
                    {
                        "$set": {
                            "status": "approved",
                            "mercadopago_payment_id": str(payment_id),
                            "approved_at": datetime.now(timezone.utc)
                        },
                        "$unset": {
                            "expires_at": ""
                        }
                    }
                )
                
                self.users_collection.update_one(
                    {"username": uid},
                    {
                        "$set": {
                            "is_free": False,
                            "plan": effective_plan,
                            "subscription_end": subscription_end,
                            "mercadopago_payment_id": str(payment_id),
                        }
                    }
                )
        
                return jsonify({
                    "message": "Payment approved and plan renewed" if subscription_is_active else "Payment approved and plan activated",
                    "status": "approved",
                    "plan": effective_plan,
                    "subscription_end": subscription_end.isoformat()
                }), 200

            except Exception:
                self.app.logger.exception('An error occurred while processing the request.')
                return self.create_error_response('An error occurred while processing the request.', 500)
                
    def run_production(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        self.app.run(debug=False, host=host, port=port, use_reloader=False)