import pytest
from fastapi.testclient import TestClient
import os
import tempfile

import database
import models
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


@pytest.fixture(autouse=True)
def in_memory_db():
    # Configure an in-memory SQLite DB for tests
    # Use a temporary file-based SQLite DB so the TestClient (running in a
    # separate thread) can see the same DB.
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_url = f"sqlite:///{tmp.name}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch the database.SessionLocal used by the app
    database.engine = engine
    database.SessionLocal = TestingSessionLocal

    # Create tables
    models.Base.metadata.create_all(bind=engine)

    yield

    # Teardown
    models.Base.metadata.drop_all(bind=engine)
    try:
        os.unlink(tmp.name)
    except Exception:
        pass


@pytest.fixture()
def client(in_memory_db):
    # ensure in_memory_db fixture runs before creating TestClient
    return TestClient(app)


def create_user(db, username, password, role):
    u = models.User(username=username, password=password, role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_create_task_invalid_category(client):
    # prepare DB and user
    db = next(database.get_db())
    student = create_user(db, "s1", "pass", "user")

    # login by setting cookie on the TestClient
    client.cookies.set("user_id", str(student.id))

    resp = client.post(
        "/tasks/create",
        data={
            "title": "Bad Cat",
            "description": "x",
            "due_date": "2099-01-01T10:00",
            "priority": "Medium",
            "category": "InvalidCat",
        },
    )
    

    # TestClient follows redirects; final page should show the flash message
    assert resp.status_code == 200
    assert "Invalid category" in resp.text


def test_create_task_valid_category_creates_task(client):
    db = next(database.get_db())
    student = create_user(db, "s2", "pass", "user")
    client.cookies.set("user_id", str(student.id))

    resp = client.post(
        "/tasks/create",
        data={
            "title": "Good Cat",
            "description": "ok",
            "due_date": "2099-01-02T11:00",
            "priority": "High",
            "category": "Homework",
        },
    )
    # final dashboard should contain the flash message
    assert resp.status_code == 200
    assert "Task created" in resp.text

    # check task exists in DB
    t = db.query(models.Task).filter(models.Task.title == "Good Cat").first()
    assert t is not None
    assert t.owner_id == student.id
    assert t.category == "Homework"


def test_edit_task_invalid_category(client):
    db = next(database.get_db())
    student = create_user(db, "s3", "pass", "user")
    # create a valid task
    due_dt = datetime.strptime("2099-01-03T12:00", "%Y-%m-%dT%H:%M")
    task = models.Task(title="T1", description="d", due_datetime=due_dt, priority="Medium", category="Chores", owner_id=student.id)
    db.add(task)
    db.commit()
    db.refresh(task)

    client.cookies.set("user_id", str(student.id))

    resp = client.post(
        f"/tasks/{task.id}/edit",
        data={
            "title": "T1",
            "description": "d",
            "due_date": "2099-01-04T12:00",
            "priority": "Low",
            "category": "BadCat",
        },
    )
    assert resp.status_code == 200
    assert "Invalid category" in resp.text


def test_admin_assign_task_category_validation(client):
    db = next(database.get_db())
    admin = create_user(db, "admin_test", "a", "admin")
    student = create_user(db, "s_student", "p", "user")

    client.cookies.set("user_id", str(admin.id))

    # invalid category
    resp = client.post(
        "/admin/assign_task",
        data={
            "title": "AdminBad",
            "target_user_id": student.id,
            "due_date": "2099-02-01T09:00",
            "priority": "High",
            "category": "Nope",
        },
    )
    assert resp.status_code == 200
    assert "Invalid category" in resp.text

    # valid category
    resp2 = client.post(
        "/admin/assign_task",
        data={
            "title": "AdminOk",
            "target_user_id": student.id,
            "due_date": "2099-02-02T09:00",
            "priority": "High",
            "category": "Exam",
        },
    )
    assert resp2.status_code == 200
    assert "Task created" in resp2.text or "Assign New Task" in resp2.text

    t = db.query(models.Task).filter(models.Task.title == "AdminOk").first()
    assert t is not None
    assert t.owner_id == student.id
    assert t.category == "Exam"
