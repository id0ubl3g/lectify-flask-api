from email_validator import validate_email, EmailNotValidError

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
        "cancel_url": [
            (r'^https://', "Cancel URL must start with https://"),
            (r'^.{1,2083}$', "Cancel URL must be between 1 and 2083 characters long"),
            (r'^https://([\w\-]+\.)+[\w\-]+(/[\w\-./?%&=]*)?$', "Cancel URL format is invalid")
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

