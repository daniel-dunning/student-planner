from fastapi import FastAPI, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import models, database, auth_utils

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
    user = db.query(models.User).filter(models.User.username == username, models.User.password == password).first()
    if not user:
        return RedirectResponse(url="/?error=Invalid", status_code=303)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response

# --- TASK & USER MANAGEMENT ---

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: models.User = Depends(get_session_user), db: Session = Depends(database.get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    # RBAC Task Filtering
    if user.role == "admin":
        tasks = db.query(models.Task).order_by(models.Task.due_datetime.asc()).all()
        students = db.query(models.User).filter(models.User.role == "student").all()
    else:
        tasks = db.query(models.Task).filter(models.Task.owner_id == user.id).order_by(models.Task.due_datetime.asc()).all()
        students = []
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "tasks": tasks, 
        "user": user, 
        "students": students, 
        "now": datetime.now()
    })

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

@app.post("/admin/add_user")
def add_user(username: str = Form(...), password: str = Form(...), user: models.User = Depends(get_session_user), db: Session = Depends(database.get_db)):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)
    # Store usernames as lowercase to keep DB canonicalization
    uname = username.lower()
    # If a user with the same canonical username exists, flash a message
    existing = db.query(models.User).filter(models.User.username == uname).first()
    if existing:
        return RedirectResponse(url="/dashboard?msg=User+already+exists", status_code=303)

    new_user = models.User(username=uname, password=password, role="student")
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/dashboard?msg=User+added", status_code=303)

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