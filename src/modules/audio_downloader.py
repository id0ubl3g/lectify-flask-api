from src.utils.return_responses import *
from src.utils.style_output import *

from typing import Dict, List, Union
from time import sleep
import yt_dlp
import sys
import os

class AudioDownloader:
    def __init__(self) -> None:
        self.output_path: str = 'src/temp'
        os.makedirs(self.output_path, exist_ok=True)

        self.ydl_opts: Dict[str, Union[str, List[Union[str, Dict[str, str]]]]] = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.output_path}/%(title)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '320'
            }],
            'postprocessor_args': [
                '-ss', '00:00:00',  
                '-t', '00:01:30'
            ]
        }

    def download_audio(self, youtube_url: str) -> dict:
        try:
            sleep(2)
            print(f'\n{BLUE}[+]{RESET} Downloading audio')
            
            devnull = open(os.devnull, 'w')
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            sys.stdout = devnull
            sys.stderr = devnull

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([youtube_url])
                extract = ydl.extract_info(youtube_url, download=True)
                audio_file_path = ydl.prepare_filename(extract)

                return create_success_return_response(f'\n{GREEN}[v]{RESET} Sucessfully downloaded', audio_file_path + '.wav')
        
        except KeyboardInterrupt:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            if devnull:
                devnull.close()

            print(f'\n{ORANGE}[!]{RESET} Operation interrupted by user')
            sys.exit(0)

        except Exception:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            if devnull:
                devnull.close()
            return create_error_return_response(f'\n{RED}[x]{RESET} Failed to download')        
        
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            if devnull:
                devnull.close()
