# URL Shortener (Flask + MySQL)

A fully functional URL Shortener built using **Flask**, **MySQL**, and
**SQLAlchemy**, supporting admin management, caching, and a clean
front-end interface.

Repository: https://github.com/vishal-benake/url_shortener_flask.git

------------------------------------------------------------------------

## 🚀 Features

-   Shorten long URLs instantly\
-   Copy-to-clipboard interface\
-   Admin dashboard to manage all URLs\
-   MySQL database integration\
-   Environment variable support using `.env`\
-   Production‑ready structure\
-   LRU cache for faster lookups\
-   Modular architecture for easy extension

------------------------------------------------------------------------

## 📦 Project Structure

    url_shortener_flask/
    │── app.py
    │── config.py
    │── models.py
    │── .env
    │── requirements.txt
    │── README.md
    │── templates/
    │   ├── index.html
    │   ├── admin.html
    │── static/
        ├── style.css

------------------------------------------------------------------------

## 🛠️ Installation & Setup Guide

Follow these steps to run the project locally:

------------------------------------------------------------------------

## 1. Clone the Repository

``` bash
git clone https://github.com/vishal-benake/url_shortener_flask.git
cd url_shortener_flask
```

------------------------------------------------------------------------

## 2. Create a Virtual Environment (Recommended)

### Windows:

``` bash
python -m venv venv
venv\Scripts\activate
```

#### For Conda:

``` bash
conda create -p myenv python==3.12 -y
conda activate ./myenv
```

### macOS / Linux:

``` bash
python3 -m venv venv
source venv/bin/activate
```

------------------------------------------------------------------------

## 3. Install Dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 4. Configure the `.env` File

Create a file named `.env` and add:

    FLASK_ENV=development
    DATABASE_URL=mysql+pymysql://root:@localhost/url_shortener
    SECRET_KEY=supersecretkey
    BASE_URL=http://localhost:5000

Modify as needed.

------------------------------------------------------------------------

## 5. Initialize MySQL Database

Open MySQL Workbench and run:

``` sql
CREATE DATABASE url_shortener;
```

The tables will auto‑create on first run.

------------------------------------------------------------------------

## 6. Run the Application

``` bash
flask run
```

Your app will be live at:

👉 http://localhost:5000

Admin panel:

👉 http://localhost:5000/admin

------------------------------------------------------------------------

# 🧪 Testing the URL Shortener

1.  Open homepage\
2.  Enter a long URL\
3.  Click **Shorten**\
4.  Copy the generated short link\
5.  Paste the short link in browser --- it should redirect

------------------------------------------------------------------------

# 🧩 Adding New Features / Contributing

We welcome contributions!

### You can help by:

-   Improving UI\
-   Adding QR code generation\
-   Adding user accounts\
-   Improving admin analytics\
-   Dockerizing the project\
-   Adding unit tests

------------------------------------------------------------------------

## How to Contribute

1.  Fork the repo\

2.  Create a new branch:

    ``` bash
    git checkout -b feature/new-idea
    ```

3.  Commit your changes:

    ``` bash
    git commit -m "Add new feature"
    ```

4.  Push and submit a Pull Request

------------------------------------------------------------------------

# 🔒 Environment Variables

Important configuration settings are stored in `.env`:

-   DB credentials\
-   Server URL\
-   Secret keys

This improves security and flexibility.

------------------------------------------------------------------------

# 🧠 Virtual Environment Explanation

A **virtual environment** keeps your project's Python dependencies
isolated.\
Benefits:

-   Avoids global package conflicts\
-   Ensures project reproducibility\
-   Allows different versions per project

Always activate `venv` before running the app.

------------------------------------------------------------------------

# 🙌 Author

Built by **Vishal Benake**\
GitHub: https://github.com/vishal-benake