from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs
import os

load_dotenv()

def initialize_mongodb():
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri, tz_aware=True)
    db = client['lectify-flask-api']

    grid_fs = gridfs.GridFS(db, collection="documents")
    documents_collection = db["documents.files"]
    documents_collection.create_index("summary_at", expireAfterSeconds=1296000)

    check_email_collection = db["check_email"]
    check_email_collection.create_index("email", unique=True)
    check_email_collection.create_index("timestamp", expireAfterSeconds=600)

    users_collection = db["users"]
    users_collection.create_index("email", unique=True)
    users_collection.create_index("username", unique=True)

    check_summarize_collection = db["check_summarize"]
    check_summarize_collection.create_index("timestamp", expireAfterSeconds=1296000)

    return {
        "client": client,
        "db": db,
        "grid_fs": grid_fs,
        "documents_collection": documents_collection,
        "check_email_collection": check_email_collection,
        "users_collection": users_collection,
        "check_summarize_collection": check_summarize_collection
    }