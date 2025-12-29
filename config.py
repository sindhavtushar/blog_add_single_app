import os
from dotenv import load_dotenv
import secrets

load_dotenv()

class Config:
    # SECRET_KEY = secrets.token_hex()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
    app.config["UPLOAD_FOLDER_USERS"] = os.environ.get("UPLOAD_FOLDER_USERS")

