# Task Management Application

A web-based Task Management Application developed using Python Flask and SQLite. It helps users organize, manage, track, and complete their daily tasks efficiently.

## Features

- User Registration and Login
- Secure Password Hashing
- Create, Read, Update and Delete Tasks
- Task Priority Management (High, Medium, Low)
- Due Date Management
- Task Categories (Work, Study, Personal, Projects, Other)
- Filter Tasks by Category
- Dashboard Statistics
- Task Completion Progress Visualization
- Subtask Management

## Technologies Used

- **Frontend:** HTML, CSS
- **Backend:** Python, Flask
- **Database:** SQLite
- **ORM:** Flask-SQLAlchemy
- **Authentication:** Werkzeug Security

## Project Structure

```text
task-management-app/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── instance/
│
├── static/
│   └── css/
│       └── style.css
│
└── templates/
    ├── dashboard.html
    ├── login.html
    └── register.html
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/reshwanth-stack/task-management-app.git
```

### 2. Navigate to the project folder

```bash
cd task-management-app
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
python app.py
```

### 7. Open in your browser

```text
http://127.0.0.1:5000
```

## Project Purpose

This project was developed as part of my Full-Stack Development Internship to improve my practical knowledge of Python, Flask, database management, authentication, and web application development.

## Author

**Reshwanth SB**

GitHub: https://github.com/reshwanth-stack

## License

This project is available for learning and educational purposes.