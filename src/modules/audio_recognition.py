from src.utils.return_responses import *

import speech_recognition as sr

class AudioRecognition:
    def __init__(self):
        self.to_recognize = sr.Recognizer()

    def recognize_audio(self, audio_path: str) -> dict:
        with sr.AudioFile(audio_path) as source:
            audio = self.to_recognize.record(source)

        audio_recognized = self.to_recognize.recognize_google(audio, language="pt-BR")
        
        return create_success_return_response(f'Audio successfully recognized', audio_recognized)
