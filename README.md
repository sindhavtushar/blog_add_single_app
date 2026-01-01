
# Blog Web Single App ⭐

A simple single-page blog web application built with Python (Flask) and basic frontend technologies (HTML, CSS, and JavaScript).  
The app lets users browse blog posts, interact with them, and rate posts using a star-based rating system.

---

## ✨ Features

- View blog posts
- Like, comment on, and share posts
- Star rating system for individual blog posts
- Static file support (CSS, JavaScript, images)
- Modular Flask backend for maintainable code
- Clean project structure using `models`, `services`, `templates`, and `static`

---

## 📁 Project Structure

```

blog_web_single_app/
│   .env
│   requirements.txt
│   .gitignore
│   app.py
│   config.py
│   database.py
│
├── models/
│   └── db_tables.py
│
├── services/
│   ├── auth_helpers.py
│   ├── blog_helpers.py
│   ├── email_service.py
│   └── token_service.py
│
├── static/
│   ├── css/
│   │   └── main.css
│   ├── images/
│   └── uploads/
│       ├── media_content/
│       └── users/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── post_detail.html
│   ├── create_post.html
│   ├── edit_post.html
│   ├── category_posts.html
│   ├── author_profile.html
│   ├── profile.html
│   ├── edit_profile.html
│   ├── rating_dashboard.html
│   ├── login.html
│   └── register.html

````

---

## ✅ Requirements

- Python 3.8 or higher  
- Flask

Install dependencies:

```bash
pip install -r requirements.txt
````

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=super-secret-key-change-this

# Database Configuration
DATABASE_URL=

# Email / SMTP Configuration
SENDER_EMAIL=
SENDER_PASSWORD=

# File Upload Configuration
UPLOAD_FOLDER=static/uploads
UPLOAD_FOLDER_USERS=static/uploads/users

```

---

## 🚀 Setup & Run

1. **Clone the repository**

```bash
git clone https://github.com/sindhavtushar/blog_add_single_app.git
cd blog_web_single_app
```

2. **Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the application**

```bash
python app.py
```

5. **Open in your browser**

Visit: `http://localhost:5000`

---

## ⭐ Star Rating Feature

The app includes a star-based rating system allowing users to rate blog posts from 1 to 5 stars.

---

## 🛠️ Built With

| Technology      | Purpose       |
| --------------- | ------------- |
| Python 🐍       | Backend       |
| Flask ⚡         | Web framework |
| HTML / CSS / JS | Frontend UI   |
| Jinja2 🌐       | Templating    |

---

## 📜 License

This project is **open source**.
You are free to use, modify, and share it.

```
