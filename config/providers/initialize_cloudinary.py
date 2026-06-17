from dotenv import load_dotenv
import cloudinary
import os

load_dotenv()

def initialize_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_SECRET_KEY'),
        secure=True
    )

    return cloudinary