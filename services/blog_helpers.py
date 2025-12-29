from flask import session
from sqlalchemy import column, select, table
from sqlalchemy.orm import joinedload
from database import db
from models.db_tables import Category, Comment, Like, Post, PostMedia, User

def get_all_blogs() -> list[Post]:
    return (
        db.session.query(Post)
        .options(
            joinedload(Post.author).joinedload(User.profile),
            joinedload(Post.category),
            joinedload(Post.media)
        )
        .order_by(Post.created_at.desc())
        .all()
    )



def get_post_by_id(post_id):
    post = (
        db.session.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.media),
            joinedload(Post.comments).joinedload(Comment.user),
            joinedload(Post.likes)
        )
        .filter(Post.id == post_id)
        .first()
    )
    return post

def get_post_media_by_post_id(post_id):
    return (
        db.session.query(PostMedia)
        .filter(PostMedia.post_id == post_id)
        .order_by(PostMedia.created_at.asc())
        .all()
    )

def add_comment(post_id, user_id, comment_msg):
    comment = Comment(
        post_id = post_id,
        user_id = user_id,
        content = comment_msg
    )
    db.session.add(comment)
    db.session.commit()
    return comment

def like_post(post_id, user_id):
    
    # check if user already like
    existing_like = Like.query.filter_by(
        post_id = post_id,
        user_id = user_id
    ).first()
    
    if existing_like:
        return False
    
    like = Like(
        post_id = post_id,
        user_id = user_id
    )
    db.session.add(like)
    db.session.commit()
    
    return True

def get_user_profile(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return None

    posts = Post.query.filter_by(author_id=user_id).order_by(Post.created_at.desc()).all()

    total_likes = 0
    total_comments = 0

    for post in posts:
        post.likes_count = len(post.likes)
        post.comments_count = len(post.comments)
        total_likes += post.likes_count
        total_comments += post.comments_count

    profile_data = {
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "posts": posts,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "user_profile_image":user.profile.profile_picture
    }

    return profile_data

def update_post(post_id, ):
    post = Post.query.filter_by(id=post).first()
    if not post:
        return False
    
def all_categories():
    return(
        db.session.query(Category)
        .all()
    )

# # ---------------Testing of functions ----------------------------------

# if __name__ == '__main__':
#     from app_copy import app
#     with app.app_context():
#         get_all_blogs()