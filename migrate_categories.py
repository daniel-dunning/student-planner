from database import SessionLocal, engine
import models

def main():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    categories = ["Homework", "Chores", "Exam", "Project", "Other"]
    for c in categories:
        if not db.query(models.Category).filter(models.Category.name == c).first():
            db.add(models.Category(name=c))
    db.commit()
    db.close()
    print("Categories migrated.")

if __name__ == "__main__":
    main()
