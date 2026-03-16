from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import models, database

def get_current_user(x_user_id: int = Header(...), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid User ID in Header")
    return user

def require_role(roles: list):
    def role_checker(user: models.User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Permission denied")
        return user
    return role_checker