import os
import secrets
from flask import Flask, render_template, url_for
from database import db
from models.db_tables import PostMedia

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex()
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")

# DB connection bind
db.init_app(app)

with app.app_context():
    db.create_all() 


@app.route('/')
def index():
    list_of_media = db.session.query(PostMedia).all()
    print('type of media from query: ',list_of_media)
    return render_template('temp.html', media = list_of_media)

