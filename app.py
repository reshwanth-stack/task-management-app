
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from sqlalchemy import inspect, text
from datetime import datetime, date
import os


# =====================================
# 1. APPLICATION CONFIGURATION
# =====================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "development-key-change-before-deployment"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmanager.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =====================================
# 2. TASK CATEGORIES
# =====================================

TASK_CATEGORIES = [
    "Work",
    "Study",
    "Personal",
    "Projects",
    "Other"
]


# =====================================
# 3. USER MODEL
# =====================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(db.String(255), nullable=False)


# =====================================
# 4. TASK MODEL
# =====================================

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False
    )

    priority = db.Column(
        db.String(20),
        default="Medium",
        nullable=False
    )

    due_date = db.Column(db.Date, nullable=True)

    category = db.Column(
        db.String(50),
        default="Other",
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # One task can have multiple subtasks.
    # Deleting a task also deletes its subtasks.

    subtasks = db.relationship(
        "SubTask",
        backref="task",
        cascade="all, delete-orphan",
        order_by="SubTask.id"
    )


# =====================================
# 5. SUBTASK MODEL — FEATURE 9
# =====================================

class SubTask(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False
    )

    task_id = db.Column(
        db.Integer,
        db.ForeignKey("task.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )


# =====================================
# 6. REGISTRATION
# =====================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception:
            db.session.rollback()
            flash(
                "Registration failed. Please try again.",
                "error"
            )

    return render_template("register.html")


# =====================================
# 7. LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password, password
        ):

            session.clear()
            session["user_id"] = user.id

            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# =====================================
# 8. DASHBOARD
# SEARCH, FILTER, SORT AND STATISTICS
# =====================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user = db.session.get(
        User,
        session["user_id"]
    )

    if user is None:
        session.clear()
        flash("Please login again.", "error")
        return redirect(url_for("login"))

    search_query = request.args.get(
        "search", ""
    ).strip()

    status_filter = request.args.get(
        "status", "all"
    )

    if status_filter not in ["all", "pending", "completed"]:
        status_filter = "all"

    sort_order = request.args.get(
        "sort", "newest"
    )

    if sort_order not in ["newest", "oldest"]:
        sort_order = "newest"

    category_filter = request.args.get(
        "category", "all"
    )

    if (
        category_filter != "all"
        and category_filter not in TASK_CATEGORIES
    ):
        category_filter = "all"

    task_query = Task.query.filter_by(
        user_id=user.id
    )

    if search_query:
        task_query = task_query.filter(
            Task.title.ilike(f"%{search_query}%")
        )

    if status_filter == "pending":
        task_query = task_query.filter_by(
            status="Pending"
        )

    elif status_filter == "completed":
        task_query = task_query.filter_by(
            status="Completed"
        )

    if category_filter != "all":
        task_query = task_query.filter_by(
            category=category_filter
        )

    if sort_order == "oldest":
        task_query = task_query.order_by(
            Task.created_at.asc()
        )
    else:
        task_query = task_query.order_by(
            Task.created_at.desc()
        )

    tasks = task_query.all()

    # =====================================
    # TASK STATISTICS
    # =====================================

    all_tasks = Task.query.filter_by(
        user_id=user.id
    ).all()

    total_tasks = len(all_tasks)

    pending_tasks = sum(
        1 for task in all_tasks
        if task.status == "Pending"
    )

    completed_tasks = sum(
        1 for task in all_tasks
        if task.status == "Completed"
    )

    high_priority_tasks = sum(
        1 for task in all_tasks
        if task.priority == "High"
    )

    today = date.today()

    overdue_tasks = sum(
        1 for task in all_tasks
        if (
            task.status == "Pending"
            and task.due_date is not None
            and task.due_date < today
        )
    )

    completion_percentage = (
        round((completed_tasks / total_tasks) * 100)
        if total_tasks > 0 else 0
    )

    return render_template(
        "dashboard.html",

        user=user,
        tasks=tasks,

        search_query=search_query,
        status_filter=status_filter,
        sort_order=sort_order,
        category_filter=category_filter,

        today=today,

        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        high_priority_tasks=high_priority_tasks,
        overdue_tasks=overdue_tasks,
        completion_percentage=completion_percentage,

        categories=TASK_CATEGORIES
    )


# =====================================
# 9. CREATE TASK
# =====================================

@app.route("/tasks/create", methods=["POST"])
def create_task():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    title = request.form.get(
        "title", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    priority = request.form.get(
        "priority", "Medium"
    )

    due_date_value = request.form.get(
        "due_date", ""
    ).strip()

    category = request.form.get(
        "category", "Other"
    )

    if not title or len(title) > 200:
        flash("Enter a valid task title.", "error")
        return redirect(url_for("dashboard"))

    if priority not in ["High", "Medium", "Low"]:
        flash("Invalid priority.", "error")
        return redirect(url_for("dashboard"))

    if category not in TASK_CATEGORIES:
        flash("Invalid task category.", "error")
        return redirect(url_for("dashboard"))

    try:
        due_date = (
            datetime.strptime(
                due_date_value, "%Y-%m-%d"
            ).date()
            if due_date_value else None
        )

    except ValueError:
        flash("Invalid due date.", "error")
        return redirect(url_for("dashboard"))

    new_task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        category=category,
        user_id=session["user_id"]
    )

    try:
        db.session.add(new_task)
        db.session.commit()
        flash("Task created successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to create task.", "error")

    return redirect(url_for("dashboard"))


# =====================================
# 10. UPDATE TASK
# =====================================

@app.route("/tasks/update/<int:task_id>", methods=["POST"])
def update_task(task_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    task = Task.query.filter_by(
        id=task_id,
        user_id=session["user_id"]
    ).first_or_404()

    title = request.form.get(
        "title", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    status = request.form.get(
        "status", "Pending"
    )

    priority = request.form.get(
        "priority", "Medium"
    )

    due_date_value = request.form.get(
        "due_date", ""
    ).strip()

    category = request.form.get(
        "category", "Other"
    )

    if not title or len(title) > 200:
        flash("Enter a valid task title.", "error")
        return redirect(url_for("dashboard"))

    if status not in ["Pending", "Completed"]:
        flash("Invalid task status.", "error")
        return redirect(url_for("dashboard"))

    if priority not in ["High", "Medium", "Low"]:
        flash("Invalid priority.", "error")
        return redirect(url_for("dashboard"))

    if category not in TASK_CATEGORIES:
        flash("Invalid task category.", "error")
        return redirect(url_for("dashboard"))

    try:
        due_date = (
            datetime.strptime(
                due_date_value, "%Y-%m-%d"
            ).date()
            if due_date_value else None
        )

    except ValueError:
        flash("Invalid due date.", "error")
        return redirect(url_for("dashboard"))

    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.due_date = due_date
    task.category = category

    try:
        db.session.commit()
        flash("Task updated successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to update task.", "error")

    return redirect(url_for("dashboard"))


# =====================================
# 11. DELETE TASK
# =====================================

@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    task = Task.query.filter_by(
        id=task_id,
        user_id=session["user_id"]
    ).first_or_404()

    try:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete task.", "error")

    return redirect(url_for("dashboard"))


# =====================================
# 12. FEATURE 9 — ADD SUBTASK
# =====================================

@app.route(
    "/tasks/<int:task_id>/subtasks/create",
    methods=["POST"]
)
def create_subtask(task_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    # Check that this task belongs to the logged-in user.

    task = Task.query.filter_by(
        id=task_id,
        user_id=session["user_id"]
    ).first_or_404()

    subtask_title = request.form.get(
        "subtask_title", ""
    ).strip()

    if not subtask_title:
        flash("Enter a subtask title.", "error")
        return redirect(url_for("dashboard"))

    if len(subtask_title) > 200:
        flash(
            "Subtask title must be 200 characters or fewer.",
            "error"
        )
        return redirect(url_for("dashboard"))

    new_subtask = SubTask(
        title=subtask_title,
        task_id=task.id
    )

    try:
        db.session.add(new_subtask)
        db.session.commit()
        flash("Subtask added successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to add subtask.", "error")

    return redirect(url_for("dashboard"))


# =====================================
# 13. FEATURE 9 — TOGGLE SUBTASK STATUS
# =====================================

@app.route(
    "/subtasks/toggle/<int:subtask_id>",
    methods=["POST"]
)
def toggle_subtask(subtask_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    # Verify that the subtask belongs to the user's task.

    subtask = (
        SubTask.query
        .join(Task)
        .filter(
            SubTask.id == subtask_id,
            Task.user_id == session["user_id"]
        )
        .first_or_404()
    )

    if subtask.status == "Completed":
        subtask.status = "Pending"
    else:
        subtask.status = "Completed"

    try:
        db.session.commit()
        flash("Subtask status updated!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to update subtask.", "error")

    return redirect(url_for("dashboard"))


# =====================================
# 14. FEATURE 9 — DELETE SUBTASK
# =====================================

@app.route(
    "/subtasks/delete/<int:subtask_id>",
    methods=["POST"]
)
def delete_subtask(subtask_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    # Verify ownership through the parent task.

    subtask = (
        SubTask.query
        .join(Task)
        .filter(
            SubTask.id == subtask_id,
            Task.user_id == session["user_id"]
        )
        .first_or_404()
    )

    try:
        db.session.delete(subtask)
        db.session.commit()
        flash("Subtask deleted successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete subtask.", "error")

    return redirect(url_for("dashboard"))


# =====================================
# 15. LOGOUT
# =====================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have logged out successfully.",
        "success"
    )

    return redirect(url_for("login"))


# =====================================
# 16. HOME
# =====================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =====================================
# 17. DATABASE INITIALIZATION
# =====================================

def initialize_database():

    with app.app_context():

        # Creates new tables, including the subtask table.
        # Existing tables and records are preserved.

        db.create_all()

        columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("task")
        }

        if "priority" not in columns:
            db.session.execute(text(
                "ALTER TABLE task ADD COLUMN "
                "priority VARCHAR(20) NOT NULL DEFAULT 'Medium'"
            ))

        if "due_date" not in columns:
            db.session.execute(text(
                "ALTER TABLE task ADD COLUMN due_date DATE"
            ))

        if "category" not in columns:
            db.session.execute(text(
                "ALTER TABLE task ADD COLUMN "
                "category VARCHAR(50) NOT NULL DEFAULT 'Other'"
            ))

        db.session.commit()

        print("Database initialized successfully!")


# =====================================
# 18. RUN APPLICATION
# =====================================

if __name__ == "__main__":

    initialize_database()

    app.run(debug=True)
