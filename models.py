from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String) # In production, use hashed passwords
    role = Column(String)     # "admin" or "student"
    tasks = relationship("Task", back_populates="owner")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    due_datetime = Column(DateTime)
    planned_start = Column(DateTime, nullable=True)
    actual_completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    priority = Column(String)
    category = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tasks")