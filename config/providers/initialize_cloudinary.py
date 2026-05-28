import cloudinary
import os

def initialize_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv('cloudinary_name'),
        api_key=os.getenv('cloudinary_api_key'),
        api_secret=os.getenv('cloudinary_api_secret'),
        secure=True
    )

    return cloudinary