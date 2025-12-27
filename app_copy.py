import os
import secrets
from slugify import slugify

from services.blog_helpers import add_comment, get_all_blogs, get_post_by_id, like_post
from services.email_service import send_email
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, login_required

from config import Config
from database import db
from models.db_tables import Category, Post, User
from services.auth_helpers import create_user, generate_email_verification_token, generate_otp_token, reset_password, verify_email_token, verify_otp_token, verify_password

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex()

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
            return redirect(url_for("index"))

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

# POST DETAIL
@app.route("/post/<int:post_id>", methods=["GET"])
def post_detail(post_id):
    post = get_post_by_id(post_id)
    print(f'[DEBUG]: {post}')
    return render_template("post_detail.html", post=post)

# CREATE POST
@app.route("/create-post", methods=["GET", "POST"])
@login_required  # Ensure only logged-in users can create posts
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        slug = slugify(title)

        new_post = Post(
            title=title,
            slug=slug,
            content=content,
            author_id=current_user.id  # <- current_user defined now
        )
        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("index"))

    return render_template("create_post.html")

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


if __name__ == "__main__":
    app.run(debug = True)