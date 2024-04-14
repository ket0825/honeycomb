from dotenv import load_dotenv
import os
from pathlib import Path
import logging


dotenv_path = Path('env/.env')
load_dotenv(dotenv_path=dotenv_path)
log_level = logging.INFO

# Get environment variables
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = int(os.getenv('DB_PORT'))
DB_NAME = os.getenv('DB_NAME')
DB_NAME = os.getenv('DB_NAME')
DB_URL = os.getenv('DB_URL')
