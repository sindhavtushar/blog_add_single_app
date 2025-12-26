from database import db
from models.db_tables import Post

def get_all_blogs() -> Post:
    return Post.query.all()
    

if __name__ == '__main__':
    get_all_blogs()