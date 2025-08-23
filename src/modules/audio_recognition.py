from src.utils.return_responses import create_success_return_response

from google.oauth2 import service_account
from pydub.utils import mediainfo
from google.cloud import speech
from dotenv import load_dotenv

import os
import io

load_dotenv()

class AudioRecognition:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(os.getenv('google-applicantion_credentials_json'))
        self.client = speech.SpeechClient(credentials=credentials)

    def recognize_audio(self, audio_path: str, language_select: str) -> dict:
        info = mediainfo(audio_path)
        sample_rate = int(info['sample_rate'])
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=sample_rate,
            language_code=language_select
        )

        with io.open(audio_path, 'rb') as file:
            content = file.read()
            audio = speech.RecognitionAudio(content=content)

        response_audio_recognized = self.client.recognize(audio=audio, config=config)
        audio_recognized = " ".join([result.alternatives[0].transcript for result in response_audio_recognized.results])
        
        return create_success_return_response(f'Audio successfully recognized', audio_recognized)

