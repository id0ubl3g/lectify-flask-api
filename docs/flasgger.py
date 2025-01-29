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
                    'tags': ['Audio Processing'],
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
                                        'description': 'Desired output format (e.g., md or pdf).',
                                        'example': 'pdf'
                                    }
                                },
                                'required': ['youtube_url', 'output_format']
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
                                    'message': 'No data provided'
                                },
                                'Missing required fields': {
                                    'message': 'Missing required fields: {missing_fields_str}'
                                },
                                'Missing YouTube URL': {
                                    'message': 'Missing YouTube URL'
                                },
                                'URL exceeds maximum length': {
                                    'message': 'URL exceeds maximum length of {self.max_url_length} characters'
                                },
                                'Invalid YouTube URL': {
                                    'message': 'Invalid YouTube URL'
                                },
                                'Unsupported format': {
                                    'message': 'Invalid format. Supported formats: {", ".join(self.valid_formats)}'
                                },
                                'File not found': {
                                    'message': 'File not found'
                                },
                                'Document conversion error': {
                                    'message': 'Error during document conversion'
                                },
                                'OS error': {
                                    'message': 'OS error occurred while handling the file'
                                },
                                'Document building error': {
                                    'message': 'Error during document building'
                                },
                                'Chat generation error': {
                                    'message': 'Error during chat generation'
                                },
                                'Unable to understand the audio': {
                                    'message': 'Unable to understand the audio'
                                },
                                'Service request error': {
                                    'message': 'Error in service request'
                                },
                                'Audio recognition error': {
                                    'message': 'Error during audio recognition'
                                },
                                'Download error': {
                                    'message': 'Download error occurred. Please check the URL and your network connection'
                                },
                                'Network error': {
                                    'message': 'Network error. Please check your internet connection'
                                },
                                'Audio downloading error': {
                                    'message': 'Error during audio downloading'
                                },
                                'Request processing error': {
                                    'message': 'An error occurred while processing the request'
                                }
                            }
                        },
                        500: {
                            'description': 'Internal server error.',
                            'examples': {
                                'Processing error': {
                                    'message': 'An error occurred while processing the request'
                                }
                            }
                        }
                    }
                }
            }
        }
    })
