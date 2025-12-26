import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

DATABASE_URL = os.getenv("DATABASE_URL")
print("Database URL:", DATABASE_URL)
