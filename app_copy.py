import datetime
import os
import secrets
import time
import uuid
from slugify import slugify

from services.blog_helpers import add_comment, get_all_blogs, get_post_by_id, get_post_media_by_post_id, get_user_profile, like_post
from services.email_service import send_email
from flask import Flask, abort, request, render_template, redirect, send_from_directory, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, login_required
from werkzeug.utils import secure_filename

from database import db
from models.db_tables import Category, Like, Post, PostMedia, User
from services.auth_helpers import create_user, generate_email_verification_token, generate_otp_token, reset_password, verify_email_token, verify_otp_token, verify_password

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex()
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")

# DB connection bind
db.init_app(app)

with app.app_context():
    db.create_all() 

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# HOME
@app.route("/")
def index():
    posts = get_all_blogs()
    print(f'[DEBUG]: Total posts: {len(posts)}')
    # file_path
    return render_template("index.html", posts=posts)

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    # Step can come from form (POST) or query string (GET)
    step = request.form.get("step") or request.args.get("step") or "1"
    email = request.form.get("email") or request.args.get("email")

    if request.method == "POST":

        # -------- STEP 1: USER DETAILS --------
        if step == "1":
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]

            if password != confirm_password:
                flash("Passwords do not match", "danger")
                return render_template("register.html", step="1")

            # Check if email already exists
            user = User.query.filter_by(email=email).first()
            if user:
                if user.is_email_verified:
                    flash("Email already registered. Please login.", "info")
                    return redirect(url_for("login"))
                else:
                    # Resend OTP if email exists but not verified
                    otp_token = generate_email_verification_token(user)
                    # Send email here
                    send_email(
                        to=user.email,
                        subject="Verify your email",
                        message=f"Your OTP is {otp_token.token}"
                    )
                    flash("OTP resent! Check your email.", "success")
                    return render_template("register.html", step="2", email=email)

            # Create new user
            new_user = create_user(username, email, password)
            otp_token = generate_email_verification_token(new_user)
            # Send email
            send_email(
                to=new_user.email,
                subject="Verify your email",
                message=f"Your OTP is {otp_token.token}"
            )
            flash("OTP sent! Check your email.", "success")
            return render_template("register.html", step="2", email=email)

        # -------- STEP 2: VERIFY OTP --------
        elif step == "2":
            input_otp = request.form["otp"]
            user = User.query.filter_by(email=email).first()

            if not user or not verify_email_token(user, input_otp):
                flash("Invalid OTP", "danger")
                return render_template("register.html", step="2", email=email)

            user.is_email_verified = True
            db.session.commit()
            flash("Email verified! You can now login.", "success")
            return redirect(url_for("login"))

    # Default: render step 1
    return render_template("register.html", step=step, email=email)

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    step = request.args.get("step")

    if request.method == "POST":
        # -------- NORMAL LOGIN --------
        if step is None:
            email = request.form["email"]
            password = request.form["password"]
            user = User.query.filter_by(email=email).first()
            if not user or not verify_password(user, password):
                flash("Invalid email or password", "danger")
                return render_template("login.html")
            if not user.is_email_verified:
                flash("Please verify email first", "warning")
                return render_template("login.html")
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for("profile"))

        # -------- FORGOT PASSWORD: EMAIL --------
        elif step == "forgot_email":
            email = request.form["email"]
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Email not found", "danger")
                return render_template("login.html", step="forgot_email")
            
            # OTP sirf yahi generate hoga
            otp_token = generate_otp_token(user, token_type="password_reset", minutes_valid=15)
            send_email(
                to=email,
                subject="Forgot Password email",
                message=f"Your OTP is {otp_token.token}"
            )
            flash("OTP sent! Check your email.", "success")
            # flash(f"OTP sent (demo): {otp_token.token}", "info")
            return render_template("login.html", step="forgot_otp", email=email)

        # -------- VERIFY OTP --------
        elif step == "forgot_otp":
            email = request.form["email"]  # hidden field se
            otp = request.form["otp"]
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("User not found", "danger")
                return redirect(url_for("login"))

            if not verify_otp_token(user, otp, token_type="password_reset"):
                flash("Invalid OTP", "danger")
                return render_template("login.html", step="forgot_otp", email=email)

            # OTP valid hai, next step reset
            return render_template("login.html", step="forgot_reset", email=email)

        # -------- RESET PASSWORD --------
        elif step == "forgot_reset":
            email = request.form["email"]
            password = request.form["password"]
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("User not found", "danger")
                return redirect(url_for("login"))

            reset_password(user, password)
            flash("Password reset successful", "success")
            return redirect(url_for("login"))

    return render_template("login.html", step=step)

# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    profile_data = get_user_profile(current_user.id)
    if not profile_data:
        return "User not found", 404

    return render_template(
        "profile.html",
        profile=profile_data,
        total_likes=profile_data['total_likes'],
        total_comments=profile_data['total_comments']
    )


# POST DETAIL
@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = get_post_by_id(post_id)
    if not post:
        abort(404)

    all_media = get_post_media_by_post_id(post_id)

    images = [m for m in all_media if m.media_type == "image"]
    videos = [m for m in all_media if m.media_type == "video"]
    audios = [m for m in all_media if m.media_type == "audio"]

    return render_template(
        "post_detail.html",
        post=post,
        images=images,
        videos=videos,
        audios=audios
    )


# CREATE POST

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "image": {"png", "jpg", "jpeg", "gif"},
    "video": {"mp4", "mov", "avi"},
    "audio": {"mp3", "wav"}
}

UPLOAD_FOLDER = 'static/uploads' # os.getenv('UPLOAD_FOLDER')
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Helper function to detect media type
def get_media_type(filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    for media_type, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return media_type
    return None

# ---------------- CREATE POST ----------------
@app.route("/create-post", methods=["GET", "POST"])
@login_required
def create_post():
    from slugify import slugify  # make sure you have python-slugify installed

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category_id = request.form.get("category_id")  # optional
        slug = slugify(title)

        # Create post
        new_post = Post(
            title=title,
            slug=slug,
            content=content,
            author_id=current_user.id,
            category_id=category_id if category_id else None
        )
        db.session.add(new_post)
        db.session.commit()  # get post.id

        # Handle file uploads
        files = request.files.getlist("media")  # multiple files support
        for file in files:
            if file and file.filename != "":
                media_type = get_media_type(file.filename)
                if not media_type:
                    flash(f"File {file.filename} has unsupported type!", "danger")
                    continue

                # Ensure upload folder exists
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

                # Create unique filename
                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                
                print(f'[Upload File Save path]: {save_path}')
                file.save(save_path)
                relative_path = f"uploads/{unique_filename}"

                # Save to DB
                media = PostMedia(
                    post_id=new_post.id,
                    file_path=relative_path,
                    media_type=media_type,
                    created_at=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                )
                db.session.add(media)

        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("index"))

    # GET request: render form
    categories = db.session.query(Category).all()  # if you have categories
    return render_template("create_post.html", categories=categories)



@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# POST COMMENT
@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def post_comment(post_id):
    comment_msg = request.form.get("comment")
    user_id = current_user.id

    if comment_msg:
        add_comment(post_id, user_id, comment_msg)
        flash("Comment added!", "success")
    else:
        flash("Comment cannot be empty", "danger")

    return redirect(url_for("post_detail", post_id=post_id))

# POST LIKE
@app.route("/post/<int:post_id>/like", methods=["POST"])
@login_required
def post_like(post_id):
    user_id = current_user.id

    if like_post(post_id, user_id):
        flash("Post liked", "success")
    else:
        flash("You already liked this post", "info")

    return redirect(url_for("post_detail", post_id=post_id))

from flask import redirect, url_for, request, flash

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    
    existing_like = Like.query.filter_by(post_id=post.id, user_id=current_user.id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        db.session.commit()
        flash("You unliked the post.", "info")
    else:
        # Like
        new_like = Like(post_id=post.id, user_id=current_user.id)
        db.session.add(new_like)
        db.session.commit()
        flash("You liked the post.", "success")
    
    # Redirect back to the same page
    return redirect(request.referrer or url_for("index"))



if __name__ == "__main__":
    app.run(debug = True)