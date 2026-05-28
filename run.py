from config.path_config import add_project_root_to_path
from dotenv import load_dotenv
from src.api.app import Server

load_dotenv()

add_project_root_to_path()

app = Server().app

if __name__ == "__main__":
    server = Server()
    server.run_production()