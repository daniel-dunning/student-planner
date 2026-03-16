from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import models, database, auth_utils

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request, 
    user_id: int = 2, # Defaulting to Son for demo; change to 1 for Admin
    db: Session = Depends(database.get_db)
):
    # Fetch user via our utility
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    # RBAC Logic inside the view
    if user.role == "admin":
        tasks = db.query(models.Task).all()
    else:
        tasks = db.query(models.Task).filter(models.Task.owner_id == user.id).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "tasks": tasks, 
        "user": user, 
        "now": datetime.now()
    })

@app.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int, 
    x_user_id: int = Form(...), 
    db: Session = Depends(database.get_db)
):
    # Re-using logic to ensure security
    user = db.query(models.User).filter(models.User.id == x_user_id).first()
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    
    if not task or (user.role != "admin" and task.owner_id != user.id):
        raise HTTPException(status_code=403, detail="Forbidden")

    task.is_completed = True
    task.actual_completed_at = datetime.now()
    db.commit()
    return RedirectResponse(url=f"/?user_id={x_user_id}", status_code=303)