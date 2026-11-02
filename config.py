# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
SQLITE_DB_PATH   = os.getenv("SQLITE_DB_PATH",   "placements.db")
MONGO_URI        = os.getenv("MONGO_URI",        "mongodb://localhost:27017/")
MONGO_DB_NAME    = os.getenv("MONGO_DB_NAME",    "placement_db")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "interview_feedbacks")