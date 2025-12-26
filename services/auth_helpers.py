import secrets
from datetime import datetime, timedelta
from database import db
from models.db_tables import User, AuthToken
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------
# PASSWORD
# -------------------
def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(user: User, password: str) -> bool:
    return check_password_hash(user.password_hash, password)

# -------------------
# USER CREATION
# -------------------
def create_user(username: str, email: str, password: str) -> User:
    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_email_verified=False
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

# -------------------
# OTP / TOKEN
# -------------------
def generate_otp_token(user: User, token_type: str = "login_otp", minutes_valid: int = 10) -> AuthToken:
    """
    token_type: 'login_otp' or 'password_reset'
    """
    token_str = str(secrets.randbelow(900000) + 100000)  # 6-digit numeric OTP
    expires_at = datetime.utcnow() + timedelta(minutes=minutes_valid)
    token = AuthToken(
        user_id=user.id,
        token=token_str,
        type=token_type,
        expires_at=expires_at,
        is_used=False
    )
    db.session.add(token)
    db.session.commit()
    return token

def verify_otp_token(user: User, otp_str: str, token_type: str = "login_otp") -> bool:
    token = (
        AuthToken.query
        .filter_by(user_id=user.id, token=otp_str, type=token_type, is_used=False)
        .first()
    )
    if token and token.expires_at > datetime.utcnow():
        token.is_used = True
        db.session.commit()
        return True
    return False

# -------------------
# PASSWORD RESET
# -------------------
def reset_password(user: User, new_password: str):
    user.password_hash = hash_password(new_password)
    db.session.commit()

def generate_email_verification_token(user: User, minutes_valid: int = 10) -> AuthToken:
    """Generates OTP for email verification."""
    return generate_otp_token(user, token_type="email_verification", minutes_valid=minutes_valid)

def verify_email_token(user: User, otp_str: str) -> bool:
    return verify_otp_token(user, otp_str, token_type="email_verification")
