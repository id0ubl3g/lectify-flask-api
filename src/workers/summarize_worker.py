from src.modules.audio_downloader import AudioDownloader
from src.modules.audio_recognition import AudioRecognition
from src.modules.document_builder import DocumentBuilder
from src.modules.convert_document import ConvertDocument
from src.modules.vertex_ai import Vertex
from src.modules.transcript_fetcher import TranscriptFetcher

from config.providers.initialize_mongodb import initialize_mongodb
from config.prompt_config import prompt_summarize
from config.input_config import MAX_SOURCE_TEXT_CHARS
from src.utils.system_utils import clean_up, sanitize_filename, create_google_credentials
from src.modules.retention import Retention

from src.rabbitmq.connection import get_connection
from datetime import datetime, timezone
from dotenv import load_dotenv
import threading
import traceback
import json
import time
import uuid
import os

RETENTION_PURGE_INTERVAL_SECONDS = 21600
GENERATIVE_AI_ATTEMPTS = 3
GENERATIVE_AI_BACKOFF_SECONDS = 2
REQUEUE_DELAY_SECONDS = 5
STARTUP_RETRY_SECONDS = 5
STARTUP_RETRY_MAX_SECONDS = 60

load_dotenv()

def call_with_retry(operation, attempts: int = GENERATIVE_AI_ATTEMPTS, backoff: float = GENERATIVE_AI_BACKOFF_SECONDS):
    for attempt in range(1, attempts + 1):
        try:
            return operation()

        except Exception as error:
            if attempt == attempts:
                raise

            print(f'message: Attempt {attempt}/{attempts} failed ({type(error).__name__}), retrying')
            time.sleep(backoff * attempt)

class Worker:
    def __init__(self) -> None:
        self.connection = get_connection()
        self.channel = self.connection.channel()

        self.channel.queue_declare(
            queue='summarize_queue',
            durable=True
        )

        mongo = initialize_mongodb()
        self.grid_fs = mongo["grid_fs"]
        self.check_summarize_collection = mongo["check_summarize_collection"]
        self.documents_collection = mongo["documents_collection"]

        self.retention = Retention(
            mongo["grid_fs"],
            mongo["documents_collection"],
            mongo["chunks_collection"],
            mongo["questions_collection"]
        )

    def start_retention_purge(self) -> None:
        def loop() -> None:
            while True:
                try:
                    result = self.retention.run()
                    print(f'message: Retention purge removed {result["expired_files"]} files, {result["expired_questions"]} questions and {result["orphan_chunks"]} orphan chunks')

                except Exception:
                    traceback.print_exc()

                time.sleep(RETENTION_PURGE_INTERVAL_SECONDS)

        threading.Thread(target=loop, daemon=True).start()

    def job_filter(self, username: str, youtube_url: str, language_select: str, output_format: str) -> dict:
        """Identifica o job: o status precisa ser por pedido, nao por usuario."""
        return {
            "username": username,
            "youtube_url": youtube_url,
            "language_select": language_select,
            "output_format": output_format
        }

    def set_status(self, job: dict | None, status: str) -> None:
        if not job:
            return

        self.check_summarize_collection.update_one(
            {"username": job["username"]},
            {"$set": {**job, "status": status, "timestamp": datetime.now(timezone.utc)}},
            upsert=True
        )

    def document_exists(self, username: str, youtube_url: str, language_select: str, output_format: str) -> bool:
        return self.documents_collection.find_one({
            "username": username,
            "youtube_url": youtube_url,
            "filetype": output_format,
            "language": language_select
        }) is not None

    def callback(self, ch, method, properties, body):
        job = None

        try:
            relative_path_audio = None
            relative_path_markdown = None
            relative_path_pdf = None

            data = json.loads(body)

            youtube_url = data['youtube_url']
            language_select = data['language_select']
            output_format = data['output_format']
            username = data['username']

            job = self.job_filter(username, youtube_url, language_select, output_format)

            if not method.redelivered and self.check_summarize_collection.find_one({**job, "status": "processing"}):
                print('message: Queue is already processing')
                ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            if self.document_exists(username, youtube_url, language_select, output_format):
                print('message: Document already exists, skipping generation')
                self.set_status(job, "success")
                ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            self.set_status(job, "processing")
            
            print(f'message: Message received: {body}')

            response_transcript = TranscriptFetcher().fetch(youtube_url, language_select)
            transcript_data = response_transcript['data'] or {}
            source_text = (transcript_data.get('text') or '').strip()

            if source_text:
                print('message: Using YouTube captions')

                os.makedirs('src/temp', exist_ok=True)

                base_name = sanitize_filename(
                    f"{transcript_data.get('title') or 'resumo'} ({uuid.uuid4().hex}) (Lectify)"
                )
                base_path = os.path.join('src/temp', base_name)

                relative_path_markdown = f'{base_path}.md'
                relative_path_pdf = f'{base_path}.pdf'

            else:
                print('message: No captions available, falling back to Speech-to-Text')

                response_audio_downloader = AudioDownloader().download_audio(youtube_url)
                relative_path_audio = (response_audio_downloader['data'])
                relative_path_markdown = relative_path_audio.replace(".mp3", ".md")
                relative_path_pdf = relative_path_audio.replace(".mp3", ".pdf")

                response_audio_recognition = call_with_retry(
                    lambda: AudioRecognition().recognize_audio(relative_path_audio, language_select)
                )
                source_text = (response_audio_recognition['data'] or '').strip()

            if not source_text:
                raise ValueError(
                    f'No transcript or speech recognized for language {language_select}'
                )

            merged_prompt = f'{prompt_summarize}{source_text[:MAX_SOURCE_TEXT_CHARS]}'

            response_generative_ai = call_with_retry(lambda: Vertex().start_chat(merged_prompt))

            expires_at = self.retention.expires_at()

            DocumentBuilder().build_document(response_generative_ai['data'], relative_path_markdown)

            ConvertDocument().markdown_to_pdf(relative_path_markdown, relative_path_pdf)

            if self.document_exists(username, youtube_url, language_select, output_format):
                print('message: Document was created by another job, skipping save')
                self.set_status(job, "success")
                ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            if output_format == 'pdf':
                with open(relative_path_pdf, 'rb') as file:
                    self.grid_fs.put(
                        file.read(),
                        filename=os.path.basename(relative_path_pdf),
                        youtube_url=youtube_url,
                        filetype='pdf',
                        language=language_select,
                        username=username,
                        summary_at=datetime.now(timezone.utc),
                        expires_at=expires_at
                    )
            if output_format == 'md':
                with open(relative_path_markdown, 'rb') as file:
                    self.grid_fs.put(
                        file.read(),
                        filename=os.path.basename(relative_path_markdown),
                        youtube_url=youtube_url,
                        filetype='md',
                        language=language_select,
                        username=username,
                        summary_at=datetime.now(timezone.utc),
                        expires_at=expires_at
                    )

            self.set_status(job, "success")

            print('message: Message processed successfully')
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception:
            traceback.print_exc()

            if not method.redelivered:
                print('message: Error during worker execution, requeueing once')
                time.sleep(REQUEUE_DELAY_SECONDS)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

                return

            self.set_status(job, "error")

            print('message: Error during worker execution, discarding message')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except KeyboardInterrupt:
            if self.channel.is_open:
                self.channel.stop_consuming()

            if self.connection.is_open:
                self.connection.close()

        finally:
            clean_up(relative_path_markdown, relative_path_pdf, relative_path_audio)
    
    def execute(self):
        self.start_retention_purge()

        self.channel.basic_consume(
            queue='summarize_queue',
            on_message_callback=self.callback
        )

        print('Awaiting messages. To exit press CTRL+C')
        self.channel.start_consuming()

def main() -> None:
    create_google_credentials()

    delay = STARTUP_RETRY_SECONDS

    while True:
        try:
            Worker().execute()

            return

        except KeyboardInterrupt:
            return

        except Exception:
            traceback.print_exc()
            print(f'message: Worker unavailable, reconnecting in {delay}s')
            time.sleep(delay)
            delay = min(delay * 2, STARTUP_RETRY_MAX_SECONDS)

if __name__ == '__main__':
    main()