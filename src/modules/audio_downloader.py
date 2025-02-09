from src.utils.return_responses import *
from src.utils.style_output import *

import yt_dlp
import random
import uuid
import os

class AudioDownloader:
    def __init__(self) -> None:
        self.output_path: str = 'src/temp'
        os.makedirs(self.output_path, exist_ok=True)

        throttled_rates = ['50K', '100K', '250K', '500K', '1M']
        self.chosen_rate: str = random.choice(throttled_rates)

        self.ydl_opts: dict[str, str | bool | int | list[str] | list[dict[str, str]]] = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.output_path}/%(title)s ({uuid.uuid4().hex}) (Lectify)',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192'
            }],
            'postprocessor_args': [
                '-ss', '00:00:00',  
                '-t', '00:01:30'
            ],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'cookiefile': 'src/temp/cookies.txt',
            'sleep_interval': random.randint(5, 10),
            'max_sleep_interval': random.randint(10, 20),
            'throttled_rate': self.chosen_rate
        }

    def download_audio(self, youtube_url: str) -> dict:
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                extract = ydl.extract_info(youtube_url, download=True)  
                audio_file_path = ydl.prepare_filename(extract).replace('.webm', '.wav')

                return create_success_return_response(f'\n{GREEN}[v]{RESET} Sucessfully downloaded', audio_file_path + '.wav')
        
        except KeyboardInterrupt:
            interruption_message()
