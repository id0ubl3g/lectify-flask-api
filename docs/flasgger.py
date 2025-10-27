from flasgger import Swagger as Flasgger
from flask import Flask

def init_flasgger(app: Flask) -> None:
    Flasgger(app, template={
        'swagger': '2.0',
        'info': {
            'title': 'Lectify Flask API',
            'version': '2.0.0',
            'description': 'AI-powered Flask API to summarize video lectures with detailed insights.'
        },
        'basePath': '/lectify',
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'JWT Authorization header using the Bearer {token} format.'
            }
        },
        'paths': {
            '/summarize': {
                'post': {
                    'tags': ['Video Summarization'],
                    'summary': 'Generates a summary of a YouTube video in MD or PDF format.',
                    'security': [{'Bearer': []}],
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'description': 'Video data and output format.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'youtube_url': {
                                        'type': 'string',
                                        'description': 'YouTube video URL.',
                                        'example': 'https://www.youtube.com/watch?v=iuPrkzJp20I'
                                    },
                                    'output_format': {
                                        'type': 'string',
                                        'enum': ['md', 'pdf'],
                                        'description': 'Desired output format.',
                                        'example': 'pdf'
                                    },
                                    'language_select': {
                                        'type': 'string',
                                        'enum': ['pt-BR', 'en-US'],
                                        'description': 'Language for recognition and summarization.',
                                        'example': 'pt-BR'
                                    }
                                },
                                'required': ['youtube_url', 'output_format', 'language_select']
                            }
                        }
                    ],
                    'responses': {
                        201: {
                            'description': 'Document generated successfully.',
                            'schema': {
                                'type': 'file',
                                'format': 'binary',
                                'description': 'Downloadable MD or PDF file.'
                            }
                        },
                        401: {
                            'description': 'Unauthorized (invalid JWT token).'
                        },
                        400: {
                            'description': 'Invalid request.',
                            'examples': {
                                'no_data': {'error': 'No data provided'},
                                'missing_fields': {'error': 'Missing required fields: youtube_url, output_format'},
                                'missing_url': {'error': 'Missing YouTube URL'},
                                'url_too_long': {'error': 'URL exceeds maximum length of 200 characters'},
                                'invalid_url': {'error': 'Invalid YouTube URL'},
                                'missing_format': {'error': 'Missing output format'},
                                'invalid_format': {'error': 'Invalid format. Supported formats: md, pdf'},
                                'missing_language': {'error': 'Missing language selection'},
                                'invalid_language': {'error': 'Invalid format. Supported formats: pt-BR, en-US'},
                                'download_error': {'error': 'Download error occurred. Please check the URL and your network connection'},
                                'network_error': {'error': 'Network error. Please check your internet connection'},
                                'audio_download_error': {'error': 'Error during audio downloading'},
                                'audio_recognition_error': {'error': 'Error during audio recognition'},
                                'chat_generation_error': {'error': 'Error during chat generation'},
                                'document_building_error': {'error': 'Error during document building'},
                                'os_error': {'error': 'OS error occurred while handling the file'},
                                'conversion_error': {'error': 'Error during document conversion'},
                                'file_not_found': {'error': 'File not found'}
                            }
                        },
                        429: {
                            'description': 'Too many requests or server busy.',
                            'examples': {
                                'busy': {'error': 'Server busy. Please try again shortly'},
                                'rate_limit': {'error': 'Too many requests. Please try again later.'},
                                'monthly_limit': {'error': 'Monthly limit exceeded or you are making too many requests. Please try again later.'},
                                'blocked': {'error': 'You have been temporarily blocked due to repeated rate limit violations. Please try again in X minute(s).'}
                            }
                        },
                        500: {
                            'description': 'Internal server error.',
                            'examples': {'error': {'error': 'An error occurred while processing the request'}}
                        }
                    }
                }
            },
            '/questions': {
                'post': {
                    'tags': ['Question Generation'],
                    'summary': 'Generates questions from an MD or PDF file.',
                    'security': [{'Bearer': []}],
                    'consumes': ['multipart/form-data'],
                    'parameters': [
                        {
                            'name': 'file',
                            'in': 'formData',
                            'type': 'file',
                            'required': True,
                            'description': 'MD or PDF file for analysis.'
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Questions generated successfully.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'questao1': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'pergunta': {'type': 'string', 'example': 'What is the correct statement about Newton\'s First Law?'},
                                                'alternativas': {
                                                    'type': 'array',
                                                    'items': {'type': 'string'},
                                                    'example': ['Question A', 'Question B']
                                                },
                                                'dica': {'type': 'string', 'example': 'Hint for the answer.'},
                                                'justificativa': {'type': 'string', 'example': 'Explanation of the correct answer.'},
                                                'resposta_correta': {'type': 'string', 'example': 'Question B'},
                                                'Dificuldade': {'type': 'string', 'example': 'Easy'}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        400: {
                            'description': 'Invalid request.',
                            'examples': {
                                'multiple_files': {'error': 'Exactly one file must be uploaded'},
                                'no_file': {'error': 'No files received'},
                                'filename_too_long': {'error': 'File name exceeds the maximum length of 200 characters.'},
                                'invalid_format': {'error': 'Invalid format. Supported formats: md, pdf'},
                                'suspicious_extension': {'error': 'The filename seems suspicious and contains a blocked extension: .exe'},
                                'invalid_mime': {'error': 'Invalid file type. Detected: text/plain. Expected: application/pdf'},
                                'extraction_error': {'error': 'Error during extraction of Markdown text'},
                                'extraction_pdf_error': {'error': 'Error during extraction of PDF text'},
                                'chat_generation_error': {'error': 'Error during chat generation'}
                            }
                        },
                        413: {
                            'description': 'File too large.',
                            'examples': {'error': {'error': 'File size exceeds the maximum limit of 5 MB.'}}
                        },
                        429: {
                            'description': 'Too many requests.',
                            'examples': {'error': {'error': 'Too many requests. Please try again later.'}}
                        },
                        500: {
                            'description': 'Internal error.',
                            'examples': {'error': {'error': 'An error occurred while processing the request'}}
                        }
                    }
                }
            },
            '/check_email_register': {
                'post': {
                    'tags': ['Authentication'],
                    'summary': 'Sends verification code via email for registration.',
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'email': {'type': 'string', 'example': 'user@example.com'}
                                },
                                'required': ['email']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Code sent.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Verification code sent to email'}}}
                        },
                        400: {
                            'description': 'Invalid or existing email.',
                            'examples': {
                                'missing_email': {'error': 'Email is required'},
                                'invalid_email': {'error': 'Invalid email format'},
                                'exists': {'error': 'Email already exists'}
                            }
                        },
                        429: {
                            'description': 'Rate limit.',
                            'examples': {'error': {'error': 'Too many requests. Please try again later.'}}
                        },
                        500: {
                            'description': 'Internal error.',
                            'examples': {'error': {'error': 'An error occurred while processing the request'}}
                        }
                    }
                }
            },
            '/verify_email_register': {
                'post': {
                    'tags': ['Authentication'],
                    'summary': 'Verifies email code for registration.',
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'email': {'type': 'string', 'example': 'user@example.com'},
                                    'code': {'type': 'string', 'example': 'ABC123'}
                                },
                                'required': ['email', 'code']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Email verified.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Email verified successfully'}}}
                        },
                        400: {
                            'description': 'Invalid code or email not found.',
                            'examples': {
                                'missing_fields': {'error': 'Email and code are required'},
                                'invalid_email': {'error': 'Invalid email format'},
                                'not_found': {'error': 'Email not found'},
                                'wrong_type': {'error': 'Invalid verification type'},
                                'invalid_code': {'error': 'Invalid verification code'}
                            }
                        },
                        404: {
                            'description': 'Email not found.',
                            'examples': {'error': {'error': 'Email not found'}}
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/register': {
                'post': {
                    'tags': ['Authentication'],
                    'summary': 'Registers a new user.',
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'username': {'type': 'string', 'example': 'user123'},
                                    'password': {'type': 'string', 'example': 'password123'},
                                    'email': {'type': 'string', 'example': 'user@example.com'},
                                    'firstname': {'type': 'string', 'example': 'John'},
                                    'lastname': {'type': 'string', 'example': 'Doe'}
                                },
                                'required': ['username', 'password', 'email', 'firstname', 'lastname']
                            }
                        }
                    ],
                    'responses': {
                        201: {
                            'description': 'User registered.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'User registered successfully'}}}
                        },
                        400: {
                            'description': 'Invalid or duplicate data.',
                            'examples': {
                                'missing_fields': {'error': 'Username, password, email, firstname and lastname are required'},
                                'exists_username': {'error': 'Username already exists'},
                                'exists_email': {'error': 'Email already exists'},
                                'not_verified': {'error': 'Email not verified'}
                            }
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/login': {
                'post': {
                    'tags': ['Authentication'],
                    'summary': 'Logs in and returns JWT tokens.',
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'username': {'type': 'string', 'example': 'user123'},
                                    'email': {'type': 'string', 'example': 'user@example.com'},
                                    'password': {'type': 'string', 'example': 'password123'}
                                }
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Login successful.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'access_token': {'type': 'string'},
                                    'refresh_token': {'type': 'string'}
                                }
                            }
                        },
                        400: {
                            'description': 'Invalid credentials.',
                            'examples': {
                                'invalid_email': {'error': 'Invalid email format'},
                                'missing_password': {'error': 'Password is required'},
                                'missing_creds': {'error': 'You must provide either a username or an email'}
                            }
                        },
                        401: {
                            'description': 'Incorrect credentials.',
                            'examples': {'error': {'error': 'Invalid email or password'}}
                        },
                        404: {
                            'description': 'User not found.',
                            'examples': {'error': {'error': 'User not found'}}
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/profile': {
                'get': {
                    'tags': ['User Profile'],
                    'summary': 'Returns user profile data.',
                    'security': [{'Bearer': []}],
                    'responses': {
                        200: {
                            'description': 'Profile loaded.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'username': {'type': 'string'},
                                    'email': {'type': 'string'},
                                    'firstname': {'type': 'string'},
                                    'lastname': {'type': 'string'},
                                    'is_free': {'type': 'boolean'},
                                    'created_at': {'type': 'string', 'format': 'date-time'},
                                    'plan': {'type': 'string'},
                                    'subscription_end': {'type': 'string', 'format': 'date-time'}
                                }
                            }
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.',
                            'examples': {'error': {'error': 'User not found'}}
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/refresh_token': {
                'post': {
                    'tags': ['Authentication'],
                    'summary': 'Refreshes access token using refresh token.',
                    'security': [{'Bearer': []}],
                    'responses': {
                        200: {
                            'description': 'Token refreshed.',
                            'schema': {'type': 'object', 'properties': {'access_token': {'type': 'string'}}}
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.'
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/update_profile': {
                'patch': {
                    'tags': ['User Profile'],
                    'summary': 'Updates user profile (name or password).',
                    'security': [{'Bearer': []}],
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'firstname': {'type': 'string', 'example': 'John'},
                                    'lastname': {'type': 'string', 'example': 'Doe'},
                                    'password': {'type': 'string', 'example': 'newpassword123'}
                                }
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Profile updated.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Profile updated successfully'}}}
                        },
                        400: {
                            'description': 'Empty or invalid fields.',
                            'examples': {
                                'empty_firstname': {'error': 'Firstname cannot be empty'},
                                'empty_lastname': {'error': 'Lastname cannot be empty'},
                                'empty_password': {'error': 'Password cannot be empty'},
                                'same_firstname': {'error': 'Firstname is the same as the current one'},
                                'same_lastname': {'error': 'Lastname is the same as the current one'},
                                'no_fields': {'error': 'No fields to update'}
                            }
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.'
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/update_image_profile': {
                'put': {
                    'tags': ['User Profile'],
                    'summary': 'Updates or removes user profile image.',
                    'security': [{'Bearer': []}],
                    'consumes': ['multipart/form-data'],
                    'parameters': [
                        {
                            'name': 'file',
                            'in': 'formData',
                            'type': 'file',
                            'required': False,
                            'description': 'Image file to upload (optional; if not provided, removes existing image).'
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Profile image updated or removed successfully.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'message': {'type': 'string', 'example': 'Profile image updated successfully'},
                                    'image_profile': {'type': 'string', 'example': 'https://cloudinary.com/'}
                                }
                            },
                            'examples': {
                                'removed': {'message': 'Profile image removed successfully'}
                            }
                        },
                        400: {
                            'description': 'Invalid format or suspicious file.',
                            'examples': {
                                'multiple_files': {'error': 'Exactly one file must be uploaded'},
                                'no_image_to_remove': {'error': 'No profile image to remove'},
                                'invalid_format': {'error': 'Invalid format. Supported formats: png, jpg, jpeg, bmp, tiff, svg, webp, heic, heif'},
                                'suspicious_extension': {'error': 'The filename seems suspicious and contains a blocked extension: .exe'},
                                'invalid_mime': {'error': 'Invalid file type. Detected: application/octet-stream. Expected: image/jpeg'}
                            }
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.',
                            'examples': {'error': {'error': 'User not found'}}
                        },
                        413: {
                            'description': 'File too large.',
                            'examples': {'error': {'error': 'File size exceeds the maximum limit of 5 MB.'}}
                        },
                        429: {
                            'description': 'Server busy or too many requests.',
                            'examples': {
                                'busy': {'error': 'Server busy. Please try again shortly'},
                                'rate_limit': {'error': 'Too many requests. Please try again later.'}
                            }
                        },
                        500: {
                            'description': 'Internal server error.',
                            'examples': {'error': {'error': 'An error occurred while processing the request'}}
                        }
                    }
                }
            },
            '/ping_email_delete_account': {
                'post': {
                    'tags': ['Account Deletion'],
                    'summary': 'Sends verification link via email for account deletion.',
                    'security': [{'Bearer': []}],
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'base_url': {'type': 'string', 'example': 'https://lectify.vercel.app'},
                                    'reset_password_page_url': {'type': 'string', 'example': 'delete-account'}
                                },
                                'required': ['base_url', 'reset_password_page_url']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Verification link sent.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Verification code sent to email'}}}
                        },
                        400: {
                            'description': 'Missing required fields.',
                            'examples': {'error': {'error': 'Base URL and Reset Password Page URL are required'}}
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.',
                            'examples': {'error': {'error': 'User not found'}}
                        },
                        429: {
                            'description': 'Rate limit or server busy.',
                            'examples': {
                                'busy': {'error': 'Server busy. Please try again shortly'},
                                'rate_limit': {'error': 'Too many requests. Please try again later.'}
                            }
                        },
                        500: {
                            'description': 'Internal error.',
                            'examples': {'error': {'error': 'An error occurred while processing the request'}}
                        }
                    }
                }
            },
            '/pong_email_delete_account': {
                'delete': {
                    'tags': ['Account Deletion'],
                    'summary': 'Verifies token and deletes user account.',
                    'security': [{'Bearer': []}],
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'token': {'type': 'string', 'example': 'abc123def456'}
                                },
                                'required': ['token']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Account deleted.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Account deleted successfully'}}}
                        },
                        400: {
                            'description': 'Invalid token or verification.',
                            'examples': {
                                'missing_token': {'error': 'Token is required'},
                                'not_found': {'error': 'Email not found'},
                                'wrong_type': {'error': 'Invalid verification type'},
                                'invalid_token': {'error': 'Invalid verification token'}
                            }
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.',
                            'examples': {'error': {'error': 'User not found'}}
                        },
                        429: {
                            'description': 'Rate limit or server busy.',
                            'examples': {
                                'busy': {'error': 'Server busy. Please try again shortly'},
                                'rate_limit': {'error': 'Too many requests. Please try again later.'}
                            }
                        },
                        500: {
                            'description': 'Internal error.',
                            'examples': {'error': {'error': 'An error occurred while processing the request'}}
                        }
                    }
                }
            },
            '/ping_email_reset_password': {
                'post': {
                    'tags': ['Password Reset'],
                    'summary': 'Sends password reset link via email.',
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'email': {'type': 'string', 'example': 'user@example.com'},
                                    'base_url': {'type': 'string', 'example': 'https://lectify.vercel.app'},
                                    'reset_password_page_url': {'type': 'string', 'example': 'reset-password'}
                                },
                                'required': ['email', 'base_url', 'reset_password_page_url']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Link sent.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Verification sent to email'}}}
                        },
                        400: {
                            'description': 'Missing data.',
                            'examples': {'error': {'error': 'Email, Base URL and Reset Password Page URL are required'}}
                        },
                        404: {
                            'description': 'Email not found.',
                            'examples': {'error': {'error': 'Email not found'}}
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/pong_email_reset_password': {
                'post': {
                    'tags': ['Password Reset'],
                    'summary': 'Verifies token and updates password.',
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'email': {'type': 'string', 'example': 'user@example.com'},
                                    'token': {'type': 'string', 'example': 'abc123def456'},
                                    'new_password': {'type': 'string', 'example': 'newPassword123'}
                                },
                                'required': ['email', 'token', 'new_password']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Password updated.',
                            'schema': {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Password reset successfully'}}}
                        },
                        400: {
                            'description': 'Invalid data.',
                            'examples': {
                                'missing': {'error': 'Email, Token, and new password are required'},
                                'not_found': {'error': 'Email not found'},
                                'wrong_type': {'error': 'Invalid verification type'},
                                'invalid_token': {'error': 'Invalid verification Token'}
                            }
                        },
                        404: {
                            'description': 'Email not found.',
                            'examples': {'error': {'error': 'Email not found'}}
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/checkout': {
                'post': {
                    'tags': ['Payments'],
                    'summary': 'Creates Stripe checkout session for paid plan.',
                    'security': [{'Bearer': []}],
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'plan': {'type': 'string', 'enum': ['1_month', '6_months', '1_year'], 'example': '1_month'},
                                    'success_url': {'type': 'string', 'example': 'https://lectify.vercel.app/success'},
                                    'cancel_url': {'type': 'string', 'example': 'https://lectify.vercel.app/cancel'}
                                },
                                'required': ['plan', 'success_url', 'cancel_url']
                            }
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Session created.',
                            'schema': {'type': 'object', 'properties': {'checkout_url': {'type': 'string'}}}
                        },
                        400: {
                            'description': 'Invalid plan or user already paid.',
                            'examples': {
                                'missing_plan': {'error': 'Plan is required'},
                                'invalid_plan': {'error': 'Plan is required'},
                                'already_paid': {'error': 'User already has a paid plan'},
                                'missing_urls': {'error': 'Success and cancel URLs are required'}
                            }
                        },
                        401: {
                            'description': 'Unauthorized.'
                        },
                        404: {
                            'description': 'User not found.'
                        },
                        429: {
                            'description': 'Rate limit.'
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            },
            '/webhook': {
                'post': {
                    'tags': ['Payments'],
                    'summary': 'Stripe webhook to process payments (internal).',
                    'consumes': ['application/json'],
                    'parameters': [],
                    'responses': {
                        200: {
                            'description': 'Processed successfully.',
                            'schema': {'type': 'object', 'properties': {'status': {'type': 'string', 'example': 'success'}}}
                        },
                        400: {
                            'description': 'Invalid payload or signature.',
                            'examples': {
                                'invalid_payload': {'error': 'Invalid payload'},
                                'invalid_sig': {'error': 'Invalid signature'}
                            }
                        },
                        500: {
                            'description': 'Internal error.'
                        }
                    }
                }
            }
        }
    })
