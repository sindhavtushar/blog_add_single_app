from flask import session
from sqlalchemy import column, select, table
from sqlalchemy.orm import joinedload
from database import db
from models.db_tables import Comment, Like, Post, User

def get_all_blogs() -> Post:
    
    # return Post.query.all()
    
    # posts = db.session.scalars(db.select(Post)).all()
    # return posts
    
    # query = """SELECT id, title, slug, content, is_published, created_at, updated_at, author_id, category_id
	# FROM public.posts;"""
    # posts = db.session.execute(query)
    # return posts

    # query = select(column('id'), column('title'), column('created_at'), column('updated_at')).select_from(table('posts'))
    # result = db.session.execute(query)
    # return result

    return (
        db.session.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category)
        )
        .all()
    )

def get_post_by_id(post_id):
    return (
        db.session.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.comments).joinedload(Comment.user),
            joinedload(Post.likes)
        )
        .filter(Post.id == post_id)
        .first()
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


# # ---------------Testing of functions ----------------------------------

# if __name__ == '__main__':
#     from app_copy import app
#     with app.app_context():
#         get_all_blogs()