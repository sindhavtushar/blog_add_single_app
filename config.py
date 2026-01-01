# config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, 'blog.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        basedir,
        os.getenv("UPLOAD_FOLDER", "static/uploads")
    )

    UPLOAD_FOLDER_USERS = os.path.join(
        basedir,
        os.getenv("UPLOAD_FOLDER_USERS", "static/uploads/users")
    )
