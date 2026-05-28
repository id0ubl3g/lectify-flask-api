from src.modules.audio_downloader import AudioDownloader
from src.modules.audio_recognition import AudioRecognition
from src.modules.document_builder import DocumentBuilder
from src.modules.convert_document import ConvertDocument
from src.modules.generative_ai import GenerativeAI

from config.providers.initialize_mongodb import initialize_mongodb
from config.prompt_config import prompt_summarize
from src.utils.system_utils import clean_up

from src.rabbitmq.connection import get_connection
from datetime import datetime, timezone
from dotenv import load_dotenv
import json
import os

load_dotenv()

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

    def callback(self, ch, method, properties, body):
        try:
            relative_path_audio = None
            relative_path_markdown = None
            relative_path_pdf = None

            data = json.loads(body)

            youtube_url = data['youtube_url']
            language_select = data['language_select']
            output_format = data['output_format']
            username = data['username']
            
            if self.check_summarize_collection.find_one({
                "username": username,
                "youtube_url": youtube_url,
                "language_select": language_select,
                "output_format": output_format,
                "status": "processing"}):
                
                print('message: Queue is already processing')
                ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            self.check_summarize_collection.update_one({
                    "username":username},
                    {
                        "$set": {
                            "status": "processing",
                            "youtube_url": youtube_url,
                            "language_select": language_select,
                            "output_format": output_format,
                            "timestamp": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
            
            print(f'message: Message received: {body}')

            response_audio_downloader = AudioDownloader().download_audio(youtube_url)
            relative_path_audio = (response_audio_downloader['data'])
            relative_path_markdown = relative_path_audio.replace(".mp3", ".md")
            relative_path_pdf = relative_path_audio.replace(".mp3", ".pdf")

            response_audio_recognition = AudioRecognition().recognize_audio(relative_path_audio, language_select)
            data_value_audio_recognition = response_audio_recognition['data']
            merged_prompt = f'{prompt_summarize}{data_value_audio_recognition}'

            response_generative_ai = GenerativeAI().start_chat(merged_prompt)

            DocumentBuilder().build_document(response_generative_ai['data'], relative_path_markdown)

            ConvertDocument().markdown_to_pdf(relative_path_markdown, relative_path_pdf)

            if output_format == 'pdf':
                with open(relative_path_pdf, 'rb') as file:
                    self.grid_fs.put(
                        file.read(),
                        filename=os.path.basename(relative_path_pdf),
                        youtube_url=youtube_url,
                        filetype='pdf',
                        language=language_select,
                        username=username,
                        summary_at=datetime.now(timezone.utc)
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
                        summary_at=datetime.now(timezone.utc)
                    )

            self.check_summarize_collection.update_one({
                    "username":username},
                    {
                        "$set": {
                            "status": "success",
                        }
                    },
                    upsert=True
                )
            
            print('message: Message processed successfully')
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            self.check_summarize_collection.update_one({
                    "username":username},
                    {
                        "$set": {
                            "status": "error"
                        }
                    },
                    upsert=True
                )
            print(f'{e}message: Error during worker execution')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        finally:
                clean_up(relative_path_markdown, relative_path_pdf, relative_path_audio)
    
    def execute(self):
        self.channel.basic_consume(
            queue='summarize_queue',
            on_message_callback=self.callback
        )

        print('Awaiting messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    worker = Worker()
    worker.execute()