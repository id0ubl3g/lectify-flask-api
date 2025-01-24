from src.utils.return_responses import *
from src.utils.style_output import *

import speech_recognition as sr
from time import sleep
import sys

class AudioRecognition:
    def recognize_audio(self, audio_path: str) -> dict:
        try:
            sleep(2)
            print(f"\n{BLUE}[+]{RESET} Recognizing audio file")

            to_recognize = sr.Recognizer()

            with sr.AudioFile(audio_path) as source:
                audio = to_recognize.record(source)

            audio_recognized = to_recognize.recognize_google(audio, language="pt-BR")
            return create_success_return_response(f'\n{GREEN}[v]{RESET} Audio successfully recognized', audio_recognized)

        except KeyboardInterrupt:
            print(f'\n{ORANGE}[!]{RESET} Operation interrupted by user')
            sys.exit(0)

        except sr.UnknownValueError:
            return create_error_return_response(f'\n{RED}[x]{RESET} Unable to understand the audio')
            
        except sr.RequestError:
            return create_error_return_response(f'\n{RED}[x]{RESET} Error in service request')
        
        except Exception:
            return create_error_return_response(f'\n{RED}[x]{RESET} Recognition failed')
