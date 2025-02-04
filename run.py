from src.utils.style_output import *
from config.path_config import *
from src.api.app import Server

add_project_root_to_path()

app = Server().app

if __name__ == "__main__":
    welcome_message()
    server = Server()
    server.run_production()