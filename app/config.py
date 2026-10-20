import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "cloud-storage-manager-default-secret-key-2025")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or None
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or None
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    DEFAULT_S3_BUCKET = os.getenv("DEFAULT_S3_BUCKET") or None
    ENABLE_DEMO_MODE = os.getenv("ENABLE_DEMO_MODE", "true").lower() in ("true", "1", "yes")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload limit
