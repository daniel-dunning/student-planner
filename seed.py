from database import SessionLocal, engine, Base
from models import User, Task
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Create Users
admin = User(username="parent", password="123", role="admin")
son = User(username="son_user", password="123", role="student")
daughter = User(username="daughter_user", password="123", role="student")

db.add_all([admin, son, daughter])
db.commit()

# 2. Create Example Tasks
tasks = [
    Task(
        title="Math Homework", 
        due_datetime=datetime.now() + timedelta(days=1), 
        priority="High", category="School", owner_id=son.id
    ),
    Task(
        title="Clean Room", 
        due_datetime=datetime.now() + timedelta(hours=5), 
        priority="Medium", category="Chores", owner_id=son.id
    ),
    Task(
        title="Biology Project", 
        due_datetime=datetime.now() + timedelta(days=3), 
        priority="High", category="School", owner_id=daughter.id
    )
]

db.add_all(tasks)
db.commit()
print("Database seeded successfully!")