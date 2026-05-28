from src.utils.return_responses import create_success_return_response

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
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128'
            }],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            "sleep_requests": True,
            "fragment_retries": 3
        }

    def download_audio(self, youtube_url: str) -> dict:
        time.sleep(random.uniform(1.5, 5.5))
        ydl_opts = self.ydl_opts.copy()
        file_uuid = uuid.uuid4().hex
        ydl_opts['outtmpl'] = f'{self.output_path}/%(title)s ({file_uuid}) (Lectify).%(ext)s'

        ydl_opts['ratelimit'] = random.randint(3_000_000, 5_000_000)
        ydl_opts['sleep_interval'] = random.uniform(2.0, 5.0)
        ydl_opts['max_sleep_interval'] = random.uniform(4.0, 10.0)
        ydl_opts['concurrent_fragment_downloads'] = 6
        ydl_opts['retries'] = 4

        ydl_opts['postprocessor_args'] = [
            '-ar', '16000',
            '-ac', '1',
            '-ss', '00:00:00',
            '-t', '00:01:30'
            ]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            extract = ydl.extract_info(youtube_url, download=True)  
            base = os.path.splitext(ydl.prepare_filename(extract))[0]
            audio_file_path = f"{base}.mp3"

            return create_success_return_response('Sucessfully downloaded',audio_file_path)