from src.utils.return_responses import create_success_return_response

from config.input_config import CAPTION_LANGUAGE_FALLBACKS
import yt_dlp
import json
import re


class TranscriptFetcher:
    def __init__(self) -> None:
        self.ydl_opts: dict[str, object] = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True
        }

    def pick_track(self, info: dict, language_select: str) -> dict | None:
        candidates = CAPTION_LANGUAGE_FALLBACKS.get(language_select, [language_select])

        for source in ('subtitles', 'automatic_captions'):
            tracks = info.get(source) or {}

            for language in candidates:
                entries = tracks.get(language) or []
                track = next((entry for entry in entries if entry.get('ext') == 'json3'), None)

                if track:
                    return track

        return None

    def parse_json3(self, raw: bytes) -> str:
        data = json.loads(raw)

        text = " ".join(
            segment.get('utf8', '')
            for event in data.get('events', [])
            for segment in (event.get('segs') or [])
        )

        return re.sub(r'\s+', ' ', text).strip()

    def fetch(self, youtube_url: str, language_select: str) -> dict:
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                title = info.get('title') or 'resumo'

                track = self.pick_track(info, language_select)

                if not track:
                    return create_success_return_response(
                        'No captions available for this video',
                        {'text': '', 'title': title}
                    )

                raw = ydl.urlopen(track['url']).read()

            return create_success_return_response(
                'Transcript fetched from captions',
                {'text': self.parse_json3(raw), 'title': title}
            )

        except Exception:
            return create_success_return_response(
                'Could not fetch captions',
                {'text': '', 'title': ''}
            )
