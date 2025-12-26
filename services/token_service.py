import secrets
from datetime import datetime, timedelta
from database import db
from models.db_tables import AuthToken

def generate_token(user_id, token_type="otp", minutes=10):
    token = secrets.token_urlsafe(8)
    auth = AuthToken(
        user_id=user_id,
        token=token,
        type=token_type,
        expires_at=datetime.utcnow() + timedelta(minutes=minutes)
    )
    db.session.add(auth)
    db.session.commit()
    return auth

def verify_token(token, token_type="otp"):
    auth = AuthToken.query.filter_by(
        token=token,
        type=token_type,
        is_used=False
    ).first()

    if auth and auth.expires_at > datetime.utcnow():
        auth.is_used = True
        db.session.commit()
        return auth.user
    return None
