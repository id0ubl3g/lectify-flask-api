from email_validator import validate_email, EmailNotValidError

from pathlib import Path
import unicodedata
import json
import sys
import re
import os

def clean_up(*file_paths: str) -> None:
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# def clean_all(folder_path: str) -> None:
#     if os.path.exists(folder_path):
#         for filename in os.listdir(folder_path):
#             file_path = os.path.join(folder_path, filename)
#             if os.path.isfile(file_path):
#                 os.remove(file_path)
            
def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    
    except EmailNotValidError:
        return False
    
def validate_user_data(data: dict) -> str | None:
    validators = {
        "username": [
            (r'^.{3,32}$', "Username must be between 3 and 32 characters."),
            (r'^[a-zA-Z0-9_]+$', "Username can only contain letters, numbers and underscores.")
        ],
        "password": [
            (r'^.{8,64}$', "Password must be at least 8 characters and max 64."),
            (r'(?=.*[a-z])', "Password must contain at least one lowercase letter."),
            (r'(?=.*[A-Z])', "Password must contain at least one uppercase letter."),
            (r'(?=.*\d)', "Password must contain at least one digit."),
            (r'(?=.*[\W_])', "Password must contain at least one special character.")
        ],
        "firstname": [
            (r'^[A-Za-z]{1,32}$', "Firstname must only contain letters and be max 32 characters.")
        ],
        "lastname": [
            (r'^[A-Za-z]{1,32}$', "Lastname must only contain letters and be max 32 characters.")
        ],
        "code": [
            (r'^[A-Za-z0-9]{6}$', "Code must be exactly 6 alphanumeric characters.")
        ],
        "token": [
            (r'^[a-f0-9]{64}$', "Token must be a 64-character hexadecimal string.")
        ],
        "success_url": [
            (r'^https://', "Success URL must start with https://"),
            (r'^.{1,2083}$', "Success URL must be between 1 and 2083 characters long"),
            (r'^https://([\w\-]+\.)+[\w\-]+(/[\w\-./?%&=]*)?$', "Success URL format is invalid")
        ],
        "failure_url": [
            (r'^https://', "Failure URL must start with https://"),
            (r'^.{1,2083}$', "Failure URL must be between 1 and 2083 characters long"),
            (r'^https://([\w\-]+\.)+[\w\-]+(/[\w\-./?%&=]*)?$', "Failure URL format is invalid")
        ],
        "pending_url": [
            (r'^https://', "Pending URL must start with https://"),
            (r'^.{1,2083}$', "Pending URL must be between 1 and 2083 characters long"),
            (r'^https://([\w\-]+\.)+[\w\-]+(/[\w\-./?%&=]*)?$', "Pending URL format is invalid")
        ]
    }

    for field, rules in validators.items():
        value = data.get(field, "")

        if value is None or str(value) == "":
            continue

        for pattern, error_msg in rules:
            if not re.match(pattern, value):
                return error_msg
            
    return None

def sanitize_filename(name: str, max_length: int = 120) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    return name[:max_length]

def create_google_credentials() -> str:
    try:
        credentials = {
            "type": os.environ["GOOGLE_TYPE"],
            "project_id": os.environ["GOOGLE_PROJECT_ID"],
            "private_key_id": os.environ["GOOGLE_PRIVATE_KEY_ID"],
            "private_key": os.environ["GOOGLE_PRIVATE_KEY"].replace("\\n", "\n"),
            "client_email": os.environ["GOOGLE_CLIENT_EMAIL"],
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "auth_uri": os.environ["GOOGLE_AUTH_URI"],
            "token_uri": os.environ["GOOGLE_TOKEN_URI"],
            "auth_provider_x509_cert_url": os.environ["GOOGLE_AUTH_PROVIDER_X509_CERT_URL"],
            "client_x509_cert_url": os.environ["GOOGLE_CLIENT_X509_CERT_URL"],
            "universe_domain": os.environ["GOOGLE_UNIVERSE_DOMAIN"],
        }

    except Exception:
        print('Error occurred while creating Google credentials')
        sys.exit(1)


    path = Path("config/lofty-entropy-465701-u3-279b20bee809.json")

    with path.open("w") as file:
        json.dump(credentials, file, indent=2)

    return path