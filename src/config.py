import os
from dotenv import load_dotenv

load_dotenv()
LOG_MORE = int(os.getenv('LOG_MORE'))

# TG
TG_API_TOKEN = os.getenv('TG_API_TOKEN')
TG_GROUP_ID = os.getenv('TG_GROUP_ID')
TG_NAME_PARSE = os.getenv('TG_NAME_PARSE')
