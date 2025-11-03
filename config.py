import os
from dotenv import load_dotenv

load_dotenv()

KIOSK_APP_URL = os.getenv("KIOSK_APP_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL")