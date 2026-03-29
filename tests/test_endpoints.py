import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
import models
import main


@pytest.fixture
def client():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch the database module to use the testing engine/session
    database.engine = engine
    database.SessionLocal = TestingSessionLocal

    # Create tables
    database.Base.metadata.create_all(bind=engine)

    with TestClient(main.app) as c:
        yield c


def test_user_create_edit_delete_flow(client):
    # Create a student directly in the test DB
    db = database.SessionLocal()
    student = models.User(username="stu_test", password="p", role="user")
    db.add(student)
    db.commit()
    db.refresh(student)

    # Authenticate by setting cookie (app uses cookie-based session)
    client.cookies.set("user_id", str(student.id))

    # Create task
    resp = client.post(
        "/tasks/create",
        data={
            "title": "Test Task",
            "description": "Created in test",
            "due_date": "2099-01-01T10:00",
            "priority": "High",
            "category": "Test",
        },
    )
    assert resp.status_code in (200, 302, 303)

    task = db.query(models.Task).filter(models.Task.owner_id == student.id).first()
    assert task is not None
    assert task.title == "Test Task"

    # Edit task
    resp = client.post(
        f"/tasks/{task.id}/edit",
        data={
            "title": "Edited Task",
            "description": "Edited",
            "due_date": "2099-01-02T11:00",
            "priority": "Medium",
            "category": "EditedCat",
        },
    )
    assert resp.status_code in (200, 302, 303)
    db.refresh(task)
    assert task.title == "Edited Task"
    assert task.priority == "Medium"

    # Delete task
    resp = client.post(f"/tasks/{task.id}/delete")
    assert resp.status_code in (200, 302, 303)
    deleted = db.query(models.Task).filter(models.Task.id == task.id).first()
    assert deleted is None
