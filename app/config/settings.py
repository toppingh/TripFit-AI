import os
from dotenv import load_dotenv

load_dotenv()

# .env 세팅
class Settings:
    TOUR_API_KEY = os.getenv("API_SERVICE_DECODING_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    BASE_URL = os.getenv("BASE_URL")
    MOBILE_OS = os.getenv("MOBILE_OS")
    MOBILE_APP = os.getenv("MOBILE_APP")
    TYPE = os.getenv("TYPE")

settings = Settings()