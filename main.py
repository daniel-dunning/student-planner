from fastapi import FastAPI, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import models, database, auth_utils

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Allowed categories for tasks (used in forms and validation)
validate_categories = ["Homework", "Chores", "Exam", "Project", "Other"]


def _flash_redirect(message: str, url: str = "/dashboard"):
    resp = RedirectResponse(url=url, status_code=303)
    resp.set_cookie(key="flash", value=message)
    return resp

# Dependency to get user from a simple Cookie-based session
def get_session_user(request: Request, db: Session = Depends(database.get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == int(user_id)).first()

# --- AUTH ROUTES ---

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        user = db.query(models.User).filter(models.User.username == username.lower()).first()
    
    if not user or not auth_utils.verify_password(password, user.password):
        return RedirectResponse(url="/?error=Invalid", status_code=303)
        
    if user.requires_password_change:
        response = RedirectResponse(url="/reset_password", status_code=303)
        response.set_cookie(key="pending_user_id", value=str(user.id))
        return response

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response

@app.get("/reset_password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.post("/reset_password")
def execute_password_reset(
    request: Request,
    new_password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    pending_user_id = request.cookies.get("pending_user_id")
    if not pending_user_id:
        return RedirectResponse(url="/", status_code=303)
        
    user = db.query(models.User).filter(models.User.id == int(pending_user_id)).first()
    if not user:
        return RedirectResponse(url="/", status_code=303)
        
    user.password = auth_utils.get_password_hash(new_password)
    user.requires_password_change = False
    db.commit()
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    response.delete_cookie("pending_user_id")
    return response

# --- TASK & USER MANAGEMENT ---

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: models.User = Depends(get_session_user), db: Session = Depends(database.get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    # RBAC Task Filtering
    if user.role == "admin":
        tasks = db.query(models.Task).order_by(models.Task.due_datetime.asc()).all()
        all_users = db.query(models.User).order_by(models.User.username.asc()).all()
        students = [u for u in all_users if u.role == "student"]
    else:
        tasks = db.query(models.Task).filter(models.Task.owner_id == user.id).order_by(models.Task.due_datetime.asc()).all()
        all_users = []
        students = []
    
    flash = request.cookies.get("flash")
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "tasks": tasks,
        "user": user,
        "students": students,
        "all_users": all_users,
        "now": datetime.now(),
        "flash": flash,
        "categories": validate_categories
    })
    if flash:
        response.delete_cookie("flash")
    return response

@app.post("/admin/assign_task")
def assign_task(
    title: str = Form(...), 
    student_id: int = Form(...), 
    due_date: str = Form(...), 
    priority: str = Form(...),
    category: str = Form(...),
    user: models.User = Depends(get_session_user), 
    db: Session = Depends(database.get_db)
):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)
    
    # Convert string from HTML datetime-local input to Python object
    due_dt = datetime.strptime(due_date, "%Y-%m-%dT%H:%M")
    # Validate category against allowed list
    if category not in validate_categories:
        return _flash_redirect("Invalid category")
    
    new_task = models.Task(
        title=title, 
        owner_id=student_id, 
        due_datetime=due_dt, 
        priority=priority, 
        category=category
    )
    db.add(new_task)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/tasks/create")
def create_task(
    title: str = Form(...),
    due_date: str = Form(...),
    priority: str = Form("Medium"),
    category: str = Form(""),
    description: str = Form(""),
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    # Only logged-in students may create their own tasks
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if user.role != "student":
        raise HTTPException(status_code=403)

    # Validate priority
    allowed_priorities = {"High", "Medium", "Low"}
    if priority not in allowed_priorities:
        return _flash_redirect("Invalid priority")

    # Validate category
    if category not in validate_categories:
        return _flash_redirect("Invalid category")



    # Parse and validate datetime-local input
    try:
        due_dt = datetime.strptime(due_date, "%Y-%m-%dT%H:%M")
    except Exception:
        return _flash_redirect("Invalid due date format")

    # Prevent creating tasks in the past
    if False:  # suspend update of past tasks
        if due_dt < datetime.now():
            return _flash_redirect("Due date must be in the future")

    # Create and persist the task
    new_task = models.Task(
        title=title,
        description=description,
        owner_id=user.id,
        due_datetime=due_dt,
        priority=priority,
        category=category
    )
    db.add(new_task)
    db.commit()
    return _flash_redirect("Task created")


@app.post("/tasks/{task_id}/edit")
def edit_task(
    task_id: int,
    title: str = Form(...),
    due_date: str = Form(...),
    priority: str = Form("Medium"),
    category: str = Form(""),
    description: str = Form(""),
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    if not user:
        return RedirectResponse(url="/", status_code=303)

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return _flash_redirect("Task not found")

    # Only owner or admin can edit
    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=403)

    # Validate priority
    allowed_priorities = {"High", "Medium", "Low"}
    if priority not in allowed_priorities:
        return _flash_redirect("Invalid priority")
    # Validate category
    if category not in validate_categories:
        return _flash_redirect("Invalid category")


    # Parse due date
    try:
        due_dt = datetime.strptime(due_date, "%Y-%m-%dT%H:%M")
    except Exception:
        return _flash_redirect("Invalid due date format")

    if due_dt < datetime.now():
        return _flash_redirect("Due date must be in the future")

    task.title = title
    task.description = description
    task.due_datetime = due_dt
    task.priority = priority
    task.category = category
    db.commit()
    return _flash_redirect("Task updated")


@app.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    if not user:
        return RedirectResponse(url="/", status_code=303)

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return _flash_redirect("Task not found")

    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=403)

    task.is_completed = True
    task.actual_completed_at = datetime.now()
    db.commit()
    return _flash_redirect("Task completed")

@app.post("/tasks/{task_id}/delete")
def delete_task(
    task_id: int,
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    if not user:
        return RedirectResponse(url="/", status_code=303)

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return _flash_redirect("Task not found")

    # Only owner or admin can delete
    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=403)

    db.delete(task)
    db.commit()
    return _flash_redirect("Task deleted")

@app.post("/admin/users/add")
def add_user(username: str = Form(...), password: str = Form(...), role: str = Form(...), user: models.User = Depends(get_session_user), db: Session = Depends(database.get_db)):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)
    uname = username.lower()
    existing = db.query(models.User).filter(models.User.username == uname).first()
    if existing:
        return _flash_redirect("User already exists")

    hashed_pwd = auth_utils.get_password_hash(password)
    new_user = models.User(username=uname, password=hashed_pwd, role=role)
    db.add(new_user)
    db.commit()
    return _flash_redirect("User added")

@app.post("/admin/users/{target_user_id}/edit")
def edit_user(
    target_user_id: int,
    username: str = Form(...),
    role: str = Form(...),
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)
        
    target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
    if target_user:
        target_user.username = username.lower()
        target_user.role = role
        db.commit()
    return _flash_redirect("User updated successfully.")

@app.post("/admin/users/{target_user_id}/delete")
def delete_user(
    target_user_id: int,
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)
    if user.id == target_user_id:
        return _flash_redirect("You cannot delete your own account.")
        
    target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
    if target_user:
        db.delete(target_user)
        db.commit()
    return _flash_redirect("User deleted successfully.")

@app.post("/admin/users/{target_user_id}/force_password_change")
def force_password_change(
    target_user_id: int,
    user: models.User = Depends(get_session_user),
    db: Session = Depends(database.get_db)
):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)
        
    target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
    if target_user:
        target_user.requires_password_change = True
        db.commit()
        return _flash_redirect(f"User {target_user.username} will be required to change their password on next login.")
    return _flash_redirect("User not found.")

@app.get("/api/calendar-events")
def get_calendar_events(
    user: models.User = Depends(get_session_user), 
    db: Session = Depends(database.get_db)
):
    if not user:
        raise HTTPException(status_code=401)
        
    query = db.query(models.Task)
    if user.role != "admin":
        query = query.filter(models.Task.owner_id == user.id)
        
    tasks = query.all()
    events = []
    
    for t in tasks:
        # Determine color based on priority
        color = "#EF4444" if t.priority == "High" else "#3B82F6" # Red vs Blue
        if t.is_completed:
            color = "#10B981" # Green for finished
            
        events.append({
            "id": t.id,
            "title": f"[{t.owner.username}] {t.title}" if user.role == "admin" else t.title,
            "start": t.due_datetime.isoformat(),
            "backgroundColor": color,
            "borderColor": color,
            "extendedProps": {
                "category": t.category,
                "status": "Completed" if t.is_completed else "Pending"
            }
        })
    return events  