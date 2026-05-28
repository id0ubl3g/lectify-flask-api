from flask_limiter import Limiter
from dotenv import load_dotenv
from redis import Redis
import os

load_dotenv()

def initialize_redis(app, key_func) -> dict:
    redis_url = os.getenv("REDIS_URL")
    redis_client = Redis.from_url(redis_url)

    limiter = Limiter(
        key_func=key_func,
        app=app,
        default_limits=["100 per minute"],
        storage_uri=redis_url
    )

    return {
        "redis_client": redis_client,
        "limiter": limiter
    }