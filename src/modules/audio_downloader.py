from src.utils.return_responses import create_success_return_response

from config.headers_config import user_agents, accept_languages

import yt_dlp
import random
import uuid
import time
import os

class AudioDownloader:
    def __init__(self) -> None:
        self.output_path: str = 'src/temp'
        os.makedirs(self.output_path, exist_ok=True)

        self.ydl_opts: dict[str, object] = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.output_path}/%(title)s ({uuid.uuid4().hex}) (Lectify)',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0'
            }],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            "sleep_requests": True,
            "fragment_retries": 3
        }

    def download_audio(self, youtube_url: str, user_is_free: bool = True) -> dict:
        time.sleep(random.uniform(1.5, 5.5))
        ydl_opts = self.ydl_opts.copy()

        if user_is_free:
            ydl_opts['ratelimit'] = random.randint(150_000, 500_000)
            ydl_opts['sleep_interval'] = random.uniform(3.0, 8.0)
            ydl_opts['max_sleep_interval'] = random.uniform(6.0, 16.0)
            ydl_opts['concurrent_fragment_downloads'] = 1
            ydl_opts['retries'] = 2

            ydl_opts['postprocessor_args'] = [
                '-ar', '16000',
                '-ac', '1',
                '-ss', '00:00:00',
                '-t', '00:01:30'
            ]
        
        else:
            ydl_opts['ratelimit'] = random.randint(3_000_000, 5_000_000)
            ydl_opts['sleep_interval'] = random.uniform(2.0, 5.0)
            ydl_opts['max_sleep_interval'] = random.uniform(4.0, 10.0)
            ydl_opts['concurrent_fragment_downloads'] = 6
            ydl_opts['retries'] = 4

            ydl_opts['postprocessor_args'] = [
                '-ar', '16000',
                '-ac', '1',
                '-ss', '00:00:00',
                '-t', '00:03:00'
            ]

        ydl_opts['http_headers'] = {
            'User-Agent': random.choice(user_agents), 
            "Accept-Language": random.choice(accept_languages),
            "Referer": "https://www.youtube.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            extract = ydl.extract_info(youtube_url, download=True)  
            audio_file_path = ydl.prepare_filename(extract).replace('.webm', '.mp3')

            return create_success_return_response('Sucessfully downloaded', f'{audio_file_path}.mp3')