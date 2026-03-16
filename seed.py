from database import SessionLocal, engine, Base
import models

Base.metadata.drop_all(bind=engine) # Clear old data
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Default Admin
admin = models.User(username="admin", password="admin", role="admin")
db.add(admin)
db.commit()
print("Database initialized. Admin user created: admin/admin")