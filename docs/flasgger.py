from flasgger import Swagger as Flasgger
from flask import Flask

def init_flasgger(app: Flask) -> None:
    Flasgger(app, template={
        'swagger': '2.0',
        'info': {
            'title': 'Lectify Flask API',
            'version': '1.0.0',
            'description': 'AI-powered API to summarize video lectures with detailed insights.'
        },
        'basePath': '',
        'paths': {
            '/lectify/summarize': {
                'post': {
                    'tags': ['Summarize'],
                    'consumes': ['application/json'],
                    'parameters': [
                        {
                            'name': 'body',
                            'in': 'body',
                            'required': True,
                            'description': 'JSON payload containing the YouTube URL and desired output format.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'youtube_url': {
                                        'type': 'string',
                                        'description': 'The URL of the YouTube video to be summarized.',
                                        'example': 'https://www.youtube.com/watch?v=iuPrkzJp20I&t=44s'
                                    },
                                    'output_format': {
                                        'type': 'string',
                                        'description': 'Desired output format (md or pdf).',
                                        'example': 'pdf'
                                    },
                                    'language_select': {
                                        'type': 'string',
                                        'description': 'Desired language for summarization (pt-BR or en-US).',
                                        'example': 'pt-BR'
                                    }
                                },
                                'required': ['youtube_url', 'output_format', 'language_select']
                            }
                        }
                    ],
                    'responses': {
                        201: {
                            'description': 'Document successfully generated and returned.',
                            'schema': {
                                'type': 'file',
                                'example': 'Generated document in the requested format.'
                            }
                        },
                        400: {
                            'description': 'Bad request due to specific errors.',
                            'examples': {
                                'No data provided': {
                                    'error': 'No data provided'
                                },
                                'Missing required fields': {
                                    'error': 'Missing required fields: {missing_fields_str}'
                                },
                                'Missing YouTube URL': {
                                    'error': 'Missing YouTube URL'
                                },
                                'URL exceeds maximum length': {
                                    'error': 'URL exceeds maximum length of {self.max_url_length} characters'
                                },
                                'Invalid YouTube URL': {
                                    'error': 'Invalid YouTube URL'
                                },
                                'Unsupported format': {
                                    'error': 'Invalid format. Supported formats: {", ".join(self.valid_formats)}'
                                },
                                'Missing language selection': {
                                    'error': 'Missing language selection'
                                },
                                'Invalid language': {
                                    'error': 'Invalid format. Supported formats: {", ".join(self.valid_languages_formats)}'
                                },
                                'File not found': {
                                    'error': 'File not found'
                                },
                                'Document conversion error': {
                                    'error': 'Error during document conversion'
                                },
                                'OS error': {
                                    'error': 'OS error occurred while handling the file'
                                },
                                'Document building error': {
                                    'error': 'Error during document building'
                                },
                                'Chat generation error': {
                                    'error': 'Error during chat generation'
                                },
                                'Unable to understand the audio': {
                                    'error': 'Unable to understand the audio'
                                },
                                'Service request error': {
                                    'error': 'Error in service request'
                                },
                                'Audio recognition error': {
                                    'error': 'Error during audio recognition'
                                },
                                'Download error': {
                                    'error': 'Download error occurred. Please check the URL and your network connection'
                                },
                                'Network error': {
                                    'error': 'Network error. Please check your internet connection'
                                },
                                'Audio downloading error': {
                                    'error': 'Error during audio downloading'
                                }
                            }
                        },
                        500: {
                            'description': 'Internal server error.',
                            'examples': {
                                'Processing error': {
                                    'error': 'An error occurred while processing the request'
                                }
                            }
                        }
                    }
                }
            },
            '/lectify/questions': {
                'post': {
                    'tags': ['Questions'],
                    'consumes': ['multipart/form-data'],
                    'parameters': [
                        {
                            'name': 'file',
                            'in': 'formData',
                            'type': 'file',
                            'required': True,
                            'description': 'The file to be processed for generating questions.',
                        }
                    ],
                    'responses': {
                        200: {
                            'description': 'Questions successfully generated from the file.',
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'questão1': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'pergunta': {
                                                    'type': 'string',
                                                    'example': 'Qual a afirmação correta sobre a Primeira Lei de Newton (Princípio da Inércia)?'
                                                },
                                                'alternativas': {
                                                    'type': 'array',
                                                    'items': {
                                                        'type': 'string',
                                                        'example': 'Um corpo em repouso só se move se uma força externa atuar sobre ele.'
                                                    },
                                                    'example': [
                                                        "Um corpo em movimento precisa de uma força contínua para manter sua velocidade.",
                                                        "Um corpo em repouso só se move se uma força externa atuar sobre ele.",
                                                        "Um corpo em movimento tende a parar naturalmente, mesmo sem forças externas.",
                                                        "A velocidade de um corpo em movimento sempre aumenta com o tempo."
                                                    ]
                                                },
                                                'dica': {
                                                    'type': 'string',
                                                    'example': 'Considere o que acontece com um objeto em movimento na ausência de forças externas.'
                                                },
                                                'justificativa': {
                                                    'type': 'string',
                                                    'example': 'A Primeira Lei de Newton diz que um corpo em repouso ou em movimento mantém seu estado, a menos que uma força externa aja sobre ele.'
                                                },
                                                'resposta_correta': {
                                                    'type': 'string',
                                                    'example': 'Um corpo em repouso só se move se uma força externa atuar sobre ele.'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        400: {
                            'description': 'Bad request due to specific errors.',
                            'examples': {
                                'No file received': {
                                    'error': 'No file received'
                                },
                                "File exceeds maximum length": {
                                    'error ': 'File name exceeds the maximum length of 100 characters'
                                },
                                'Invalid format': {
                                    'error': 'Invalid format. Supported formats: {", ".join(self.valid_formats)}'
                                },
                                'Suspicious file name': {
                                    'error': 'The filename seems suspicious and contains a blocked extension: {extensions}'
                                },
                                'Invalid file type': {
                                    'error': 'Invalid file type. Detected: {detected_mime_type}. Expected: {expected_mime_type}'
                                },
                                'Chat generation error': {
                                    'error': 'Error during chat generation'
                                },
                                'Extraction error': {
                                    'error': 'Error during text extraction from the file'
                                }
                            }
                        },
                        413: {
                            'description': 'Payload Too Large - File size exceeds the maximum allowed limit.',
                            'examples': {
                                'File size exceeds 5MB': {
                                    'error': 'File size exceeds the maximum limit of 5 MB'
                                }
                            }
                        },
                        500: {
                            'description': 'Internal server error.',
                            'examples': {
                                'Processing error': {
                                    'error': 'An error occurred while processing the request'
                                }
                            }
                        }
                    }
                }
            }
        }
    })
