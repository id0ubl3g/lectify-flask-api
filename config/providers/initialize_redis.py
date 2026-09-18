from flask_limiter import Limiter
from dotenv import load_dotenv
from flask import request
from redis import Redis
import os

load_dotenv()

def initialize_redis(app, key_func) -> dict:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    port_env = os.getenv("REDIS_PORT")
    redis_port = int(port_env) if port_env and port_env.isdigit() else 6379
    
    redis_username = os.getenv("REDIS_USERNAME") or "default"
    redis_password = os.getenv("REDIS_PASSWORD", "")

    if redis_password:
        redis_url = f"redis://{redis_username}:{redis_password}@{redis_host}:{redis_port}"
    else:
        redis_url = f"redis://{redis_host}:{redis_port}"

    redis_client = Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        username=redis_username,
        password=redis_password if redis_password else None
    )

    limiter = Limiter(
        key_func=key_func,
        app=app,
        default_limits=["100 per minute"],
        storage_uri=redis_url
    )

    limiter.request_filter(lambda: request.method == "OPTIONS")

    return {
        "redis_client": redis_client,
        "limiter": limiter
    }