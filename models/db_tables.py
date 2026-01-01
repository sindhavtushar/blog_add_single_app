import uuid
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import (
    CheckConstraint, Column, String, Integer, Boolean, Text, DateTime,
    ForeignKey, UniqueConstraint, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import db


# USERS

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(), nullable=False)
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete")
    comments = relationship("Comment", back_populates="user", cascade="all, delete")
    likes = relationship("Like", back_populates="user", cascade="all, delete")
    ratings = relationship("Rating", back_populates="user")
    tokens = relationship("AuthToken", back_populates="user", cascade="all, delete")
    sessions = relationship("Session", back_populates="user", cascade="all, delete")
    # One-to-one profile relationship
    profile = db.relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan"
    )

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    
    bio = Column(String(255))
    about = Column(Text)
    profile_picture = Column(String(500))  # URL or file path
    cover_photo = Column(String(500))
    website = Column(String(255))
    location = Column(String(150))
    
    gender = Column(
        Enum("male", "female", "other", "prefer_not_to_say", name="gender_types"),
        default="prefer_not_to_say",
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship("User", back_populates="profile")

# followers = db.Table(
#     "followers",
#     db.Column("follower_id", UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
#     db.Column("followed_id", UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
#     db.Column("timestamp", db.DateTime, default=datetime.utcnow)
# )

# AUTH TOKENS

class AuthToken(db.Model):
    __tablename__ = "auth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tokens")


# SESSIONS

class Session(db.Model):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")


# CATEGORIES

class Category(db.Model):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    posts = relationship("Post", back_populates="category")


# POSTS

class Post(db.Model):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    media = relationship("PostMedia", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete")
    likes = relationship("Like", back_populates="post", cascade="all, delete")
    ratings = relationship("Rating", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")


# POST MEDIA

class PostMedia(db.Model):
    __tablename__ = "post_media"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    media_type = Column(Enum("image", "video", "audio", name="media_types"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="media")


# TAGS

class Tag(db.Model):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    posts = relationship("Post", secondary="post_tags", back_populates="tags")


# POST_TAGS

class PostTag(db.Model):
    __tablename__ = "post_tags"

    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)


# COMMENTS

class Comment(db.Model):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")


# LIKES

class Like(db.Model):
    __tablename__ = "likes" 

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_user_post_like"),
    )

# Rating Model

class Rating(db.Model):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    rating = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="rating_range_check"
        ),
        UniqueConstraint(
            "post_id",
            "user_id",
            name="unique_user_post_rating"
        ),
    )

    # Relationships
    post = relationship("Post", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

    def __repr__(self):
        return f"<Rating {self.rating}>"
