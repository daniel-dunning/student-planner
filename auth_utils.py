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
import bcrypt

def verify_password(plain_password, hashed_password):
    try:
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
    except ValueError:
        # In case the database holds an old plain-text password or an invalid format
        # Decoded as best-effort for equality
        decoded_hash = hashed_password.decode('utf-8') if isinstance(hashed_password, bytes) else hashed_password
        return plain_password == decoded_hash

def get_password_hash(password):
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')