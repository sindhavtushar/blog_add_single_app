# Blog Web Single App ⭐

A simple blog application built using Python (Flask) and basic frontend tech (HTML/CSS/JS).  
This project allows users to view blog posts and rate them using stars.

---

## 🧠 Features

- 📄 **View blog posts**
- ❤️ **like, comment and share**
- ⭐ **Star rating component** to rate individual posts
- 🖼️ Static files support (CSS / JS)
- 🧩 Modular Python backend using Flask
- 🔧 Keeps code structured in `models`, `services`, `templates`, and `static`

---

## 🗂️ Folder Structure

```

blog_web_single_app/
│   .env
|   Requirements
│   .gitignore
│   app.py
│   config.py
│   database.py
│
├───models
│   │   db_tables.py
│   │
├───services
│   │   auth_helpers.py
│   │   blog_helpers.py
│   │   email_service.py
│   │   token_service.py
│   │
├───static
│   ├───css
│   │       main.css
│   │
│   ├───images
│   └───uploads
│       ├───media_content
│       └───users
│
├───templates
│       author_profile.html
│       base.html
│       category_posts.html
│       create_post.html
│       edit_post.html
│       edit_profile.html
│       index.html
│       login.html
│       post_detail.html
│       profile.html
│       rating_dashboard.html
│       register.html

Before running the app, make sure you have:

- 🐍 Python 3.8+
- 📦 Flask

```

You can install required packages with:

```bash
pip install -r requirements.txt
````


## 🚀 Setup & Run

## Environment Variables 

Create a `.env` file in the root directory:

  ```bash
  FLASK_ENV=development
  SECRET_KEY=your-secret-key
  DATABASE_URL=sqlite:///blog.db
  UPLOAD_FOLDER=static/uploads
  UPLOAD_FOLDER_USERS=static/uploads/users
   ```

1. **Clone the repo**

   ```bash
   git clone https://github.com/sindhavtushar/blog_add_single_app.git
   cd blog_web_single_app
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**

   ```bash
   python app.py
   ```

5. **Open in browser**

   Visit: `http://localhost:5000`

---

## ⭐ Star Rating Feature

The app includes a **star rating UI** where users can rate blog posts (e.g., 1–5 stars).

---

## 🛠 Built With

| Technology  | Purpose     |
| ----------- | ----------- |
| Python 🐍   | Backend     |
| Flask ⚡️    | HTTP Server |
| HTML/CSS/JS | Frontend    |
| Jinja2 🌐   | Templates   |

---

---

## 📜 License

This project is open-source — feel free to use/edit/share!

```
