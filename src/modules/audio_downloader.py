from src.utils.return_responses import *
from src.utils.style_output import *

from typing import Dict, List, Union
import yt_dlp
import uuid
import os

class AudioDownloader:
    def __init__(self) -> None:
        self.output_path: str = 'src/temp'
        os.makedirs(self.output_path, exist_ok=True)

        self.ydl_opts: Dict[str, Union[str, bool, List[Union[str, Dict[str, str]]]]] = {
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
            'no_warnings': True ,
            'noplaylist': True
        }

    def download_audio(self, youtube_url: str) -> dict:
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                extract = ydl.extract_info(youtube_url, download=True)
                
                audio_file_path = ydl.prepare_filename(extract).replace('.webm', '.wav')

                return create_success_return_response(f'\n{GREEN}[v]{RESET} Sucessfully downloaded', audio_file_path + '.wav')
        
        except KeyboardInterrupt:
            interruption_message()

