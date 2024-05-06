from dotenv import load_dotenv
import os
from pathlib import Path

dotenv_path = Path('env/.env')
load_dotenv(dotenv_path=dotenv_path)

# Get environment variables
# STAGE = os.getenv('STAGE')

# if STAGE == 'dev':
#     DB_USER = os.getenv('DEV_DB_USER')
#     DB_PASSWORD = os.getenv('DEV_DB_PASSWORD')
#     DB_PORT = int(os.getenv('DEV_DB_PORT'))
#     DB_NAME = os.getenv('DEV_DB_NAME')
#     DB_HOST = os.getenv('DEV_DB_HOST')
# elif STAGE == 'prod':
#     DB_USER = os.getenv('DB_USER')
#     DB_PASSWORD = os.getenv('DB_PASSWORD')
#     DB_PORT = int(os.getenv('DB_PORT'))
#     DB_NAME = os.getenv('DB_NAME')
#     DB_HOST = os.getenv('DB_HOST')

DB_USER = os.getenv('DEV_DB_USER')
DB_PASSWORD = os.getenv('DEV_DB_PASSWORD')
DB_PORT = int(os.getenv('DEV_DB_PORT'))
DB_NAME = os.getenv('DEV_DB_NAME')
DB_HOST = os.getenv('DEV_DB_HOST')

