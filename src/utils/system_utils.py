from typing import Optional, Dict
import os

def clean_up(*file_paths: Optional[str]) -> None:
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
