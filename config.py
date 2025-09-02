import os
from dotenv import load_dotenv

load_dotenv()

SCRAPESTORM_API_KEY = os.getenv("SCRAPESTORM_API_KEY")
SCRAPESTORM_BASE_URL = os.getenv("SCRAPESTORM_BASE_URL", "http://localhost:8080/api")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL_NAME")