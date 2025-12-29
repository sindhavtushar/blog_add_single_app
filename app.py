import datetime
import os
import secrets
import time
import uuid
from slugify import slugify

from services.blog_helpers import add_comment, all_categories, get_all_blogs, get_post_by_id, get_post_media_by_post_id, get_user_profile, like_post
from services.email_service import send_email
from flask import Flask, abort, request, render_template, redirect, send_from_directory, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, login_required
from werkzeug.utils import secure_filename

from database import db
from models.db_tables import Category, Like, Post, PostMedia, User, UserProfile
from services.auth_helpers import create_user, generate_email_verification_token, generate_otp_token, reset_password, verify_email_token, verify_otp_token, verify_password

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex()


# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "image": {"png", "jpg", "jpeg", "gif"},
    "video": {"mp4", "mov", "avi"},
    "audio": {"mp3", "wav"}
}

UPLOAD_FOLDER = "D:/VisioByte/frameworks/flask/project/blog_app_single_app/T_APP/static/uploads"
UPLOAD_FOLDER_USERS = "D:/VisioByte/frameworks/flask/project/blog_app_single_app/T_APP/static/uploads/users"

# DB connection bind
db.init_app(app)

with app.app_context():
    db.create_all() 

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)



@app.route("/")
def index():
    posts = get_all_blogs()
    
    # Filter out posts authored by the current user if logged in
    if current_user.is_authenticated:
        posts = [post for post in posts if post.author_id != current_user.id]
    
    return render_template("index.html", posts=posts)


# # HOME
# @app.route("/")
# def index():
#     posts = get_all_blogs()
#     return render_template("index.html", posts=posts)
    # print(f'[DEBUG]: Total posts: {len(posts)}')
    # file_path
    # return render_template('test.html', posts=posts)
    # categories = all_categories()
    # return render_template('test.html', categories=categories, posts=posts)

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    step = request.form.get("step") or request.args.get("step") or "1"
    email = request.form.get("email") or request.args.get("email")

    # -------- HANDLE POST REQUEST --------
    if request.method == "POST":

        # -------- STEP 1: USER DETAILS --------
        if step == "1":
            username = request.form["username"].strip()
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]

            # Password mismatch
            if password != confirm_password:
                flash("Passwords do not match", "danger")
                return render_template("register.html", step="1", username=username, email=email)

            existing_user = User.query.filter_by(email=email).first()

            # Email already exists
            if existing_user:
                if existing_user.is_email_verified:
                    flash("Email already registered. Please login.", "info")
                    return redirect(url_for("login"))
                else:
                    # Resend OTP for unverified user
                    otp_token = generate_email_verification_token(existing_user)
                    send_email(
                        to=existing_user.email,
                        subject="Verify your email",
                        message=f"Your OTP is {otp_token.token}"
                    )
                    flash("OTP resent! Check your email.", "success")
                    return render_template("register.html", step="2", email=email)

            # Create new user
            new_user = create_user(username, email, password)

            # Send OTP
            otp_token = generate_email_verification_token(new_user)
            send_email(
                to=new_user.email,
                subject="Verify your email",
                message=f"Your OTP is {otp_token.token}"
            )

            flash("OTP sent! Check your email.", "success")
            return render_template("register.html", step="2", email=email)

        # -------- STEP 2: VERIFY OTP OR RESEND --------
        elif step == "2":
            # Resend OTP button clicked
            if request.form.get("resend_otp"):
                user = User.query.filter_by(email=email).first()
                if user and not user.is_email_verified:
                    otp_token = generate_email_verification_token(user)
                    send_email(
                        to=user.email,
                        subject="Verify your email",
                        message=f"Your OTP is {otp_token.token}"
                    )
                    flash("OTP resent! Check your email.", "success")
                return render_template("register.html", step="2", email=email)

            # Normal OTP verification
            input_otp = request.form.get("otp")
            user = User.query.filter_by(email=email).first()

            if not user or not verify_email_token(user, input_otp):
                flash("Invalid OTP", "danger")
                return render_template("register.html", step="2", email=email)

            # Mark email as verified
            user.is_email_verified = True
            db.session.commit()

            flash("Email verified! You can now login.", "success")
            return redirect(url_for("login"))

    # -------- HANDLE GET REQUEST --------
    return render_template("register.html", step=step, email=email)

@app.route("/login", methods=["GET", "POST"])
def login():
    step = request.args.get("step")  # None | forgot_email | forgot_otp | forgot_reset

    # ---------------- GET REQUEST ----------------
    if request.method == "GET":
        return render_template("login.html", step=step)

    # ---------------- POST REQUEST ----------------

    # ========== NORMAL LOGIN ==========
    if step is None:
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not verify_password(user, password):
            flash("Invalid email or password", "danger")
            return render_template("login.html", step=None, email=email)

        if not user.is_email_verified:
            flash("Please verify your email first", "warning")
            return render_template("login.html", step=None, email=email)

        login_user(user)
        flash("Login successful", "success")
        return redirect(url_for("profile"))

    # ========== FORGOT PASSWORD: EMAIL ==========
    if step == "forgot_email":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not found", "danger")
            return render_template("login.html", step="forgot_email", email=email)

        otp_token = generate_otp_token(
            user,
            token_type="password_reset",
            minutes_valid=15
        )

        send_email(
            to=email,
            subject="Password Reset OTP",
            message=f"Your OTP is {otp_token.token}"
        )

        flash("OTP sent. Check your email.", "success")
        return render_template("login.html", step="forgot_otp", email=email)

    # ========== VERIFY OTP ==========
    if step == "forgot_otp":
        email = request.form.get("email", "")
        otp = request.form.get("otp", "")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found", "danger")
            return redirect(url_for("login"))

        if not verify_otp_token(user, otp, token_type="password_reset"):
            flash("Invalid or expired OTP", "danger")
            return render_template("login.html", step="forgot_otp", email=email)

        return render_template("login.html", step="forgot_reset", email=email)

    # ========== RESET PASSWORD ==========
    if step == "forgot_reset":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found", "danger")
            return redirect(url_for("login"))

        reset_password(user, password)
        flash("Password reset successful. Please login.", "success")
        return redirect(url_for("login"))

    # ---------------- FALLBACK ----------------
    return redirect(url_for("login"))


# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("index"))


@app.route("/author/<username>")
def author_profile(username):
    # Get user by username
    profile = User.query.filter_by(username=username).first_or_404()

    # Check if current user is viewing own profile
    is_owner = current_user.is_authenticated and current_user.id == profile.id

    return render_template(
        "author_profile.html",
        profile=profile,
        is_owner=is_owner
    )





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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    profile = current_user.profile

    if request.method == "POST":
        # ---------- USERNAME (User model) ----------
        new_username = request.form.get("username", "").strip()

        if new_username and new_username != current_user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash("Username already taken. Please choose another one.", "danger")
                return redirect(url_for("edit_profile"))

            current_user.username = new_username

        # ---------- PROFILE TEXT FIELDS ----------
        profile.bio = request.form.get("bio", "")
        profile.about = request.form.get("about", "")
        profile.location = request.form.get("location", "")
        profile.website = request.form.get("website", "")
        profile.gender = request.form.get("gender", "prefer_not_to_say")

        # ---------- PROFILE MEDIA ----------
        files = request.files.getlist("media")
        for file in files:
            if file and file.filename:
                media_type = get_media_type(file.filename)
                if not media_type:
                    flash(f"File {file.filename} has unsupported type!", "danger")
                    continue

                os.makedirs(UPLOAD_FOLDER_USERS, exist_ok=True)

                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                save_path = os.path.join(UPLOAD_FOLDER_USERS, unique_filename)
                file.save(save_path)

                profile.profile_picture = f"uploads/users/{unique_filename}"

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", profile=profile)


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
        slug = slugify(title)

        category_id = request.form.get("category_id")
        new_category_name = request.form.get("new_category").strip()

        if new_category_name:
            # Check if category already exists
            existing = Category.query.filter_by(name=new_category_name).first()
            if existing:
                category_id = existing.id
            else:
                new_cat = Category(name=new_category_name)
                db.session.add(new_cat)
                db.session.commit()
                category_id = new_cat.id


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
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                # Create unique filename
                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                
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
    return send_from_directory(UPLOAD_FOLDER, filename)


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


# @app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
# @login_required
# def edit_post(post_id):
#     # Get the post
#     post = Post.query.get_or_404(post_id)

#     # Security check
#     if post.author != current_user:
#         abort(403)

#     # Get media for display
#     all_media = get_post_media_by_post_id(post_id)
#     images = [m for m in all_media if m.media_type == "image"]
#     videos = [m for m in all_media if m.media_type == "video"]
#     audios = [m for m in all_media if m.media_type == "audio"]

#     if request.method == "POST":
#         # Form fields
#         title = request.form["title"]
#         content = request.form["content"]
#         category_id = request.form.get("category_id")  # optional, existing category select
#         new_category_name = request.form.get("new_category")  # optional, new category input
#         remove_image = request.form.get("remove_image")  # checkbox
#         slug = slugify(title)
#         post.updated_at = datetime.datetime.now(datetime.timezone.utc)

#         # Handle category
#         if new_category_name and new_category_name.strip():
#             # Check if category already exists (case-insensitive)
#             existing_category = Category.query.filter(
#                 db.func.lower(Category.name) == new_category_name.strip().lower()
#             ).first()
#             if existing_category:
#                 post.category_id = existing_category.id
#             else:
#                 # Create new category
#                 new_cat = Category(name=new_category_name.strip())
#                 db.session.add(new_cat)
#                 db.session.commit()  # commit to get new_cat.id
#                 post.category_id = new_cat.id
#         elif category_id:
#             post.category_id = category_id
#         else:
#             post.category_id = None

#         # Update post fields
#         post.title = title
#         post.slug = slug
#         post.content = content
#         db.session.commit()

#     return render_template(
#         "edit_post.html",
#         post=post,
#         images=images,
#         videos=videos,
#         audios=audios
#     )


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Security check
    if post.author != current_user:
        abort(403)

    # Get media for display
    all_media = get_post_media_by_post_id(post_id)
    images = [m for m in all_media if m.media_type == "image"]
    videos = [m for m in all_media if m.media_type == "video"]
    audios = [m for m in all_media if m.media_type == "audio"]

    # Fetch all categories for dropdown
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category_id = request.form.get("category_id")
        new_category_name = request.form.get("new_category")
        remove_image = request.form.get("remove_image")
        slug = slugify(title)
        post.updated_at = datetime.datetime.now(datetime.timezone.utc)

        # Handle category
        if new_category_name and new_category_name.strip():
            existing_category = Category.query.filter(
                db.func.lower(Category.name) == new_category_name.strip().lower()
            ).first()
            if existing_category:
                post.category_id = existing_category.id
            else:
                new_cat = Category(name=new_category_name.strip())
                db.session.add(new_cat)
                db.session.commit()
                post.category_id = new_cat.id
        elif category_id:
            post.category_id = category_id
        else:
            post.category_id = None

        # Update post fields
        post.title = title
        post.slug = slug
        post.content = content
        db.session.commit()

        # Handle image upload
        uploaded_file = request.files.get("image")
        if uploaded_file and uploaded_file.filename != "":
            media_type = get_media_type(uploaded_file.filename)
            if not media_type:
                flash(f'File {uploaded_file.filename} has unsupported type!', 'danger')
            else:
                # Remove old images
                for img in images:
                    old_path = os.path.join(UPLOAD_FOLDER, img.file_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    db.session.delete(img)

                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(uploaded_file.filename)}"
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                uploaded_file.save(save_path)
                relative_path = f"uploads/{unique_filename}"

                new_media = PostMedia(
                    post_id=post.id,
                    file_path=relative_path,
                    media_type=media_type,
                    created_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.session.add(new_media)
                db.session.commit()

        # Handle remove image checkbox
        elif remove_image:
            for img in images:
                old_path = os.path.join(UPLOAD_FOLDER, img.file_path)
                if os.path.exists(old_path):
                    os.remove(old_path)
                db.session.delete(img)
            db.session.commit()

        flash("Post updated successfully!", "success")
        return redirect(url_for("post_detail", post_id=post.id))

    return render_template(
        "edit_post.html",
        post=post,
        images=images,
        videos=videos,
        audios=audios,
        categories=categories
    )



@app.route("/post/<int:post_id>/delete", methods=["GET", "POST"])
@login_required
def delete_post(post_id):
    return f'Delete page'
    

if __name__ == "__main__":
    app.run(debug = True, host="0.0.0.0")