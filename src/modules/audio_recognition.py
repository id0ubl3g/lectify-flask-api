from src.utils.return_responses import *
from src.utils.style_output import *

import speech_recognition as sr

class AudioRecognition:
    def __init__(self):
        self.to_recognize = sr.Recognizer()

    def recognize_audio(self, audio_path: str) -> dict:
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.to_recognize.record(source)

            audio_recognized = self.to_recognize.recognize_google(audio, language="pt-BR")
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Audio successfully recognized', audio_recognized)

        except KeyboardInterrupt:
            interruption_message()

        except sr.UnknownValueError:
            custom_error_message('Unable to understand the audio')
            
        except sr.RequestError:
            custom_error_message('Error in service request')
        
        except Exception:
            exception_error('audio recognition')
