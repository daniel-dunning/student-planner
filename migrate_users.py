import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def migrate():
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    
    # Hash existing passwords
    print("Checking and hashing passwords...")
    cursor.execute("SELECT id, password FROM users")
    users = cursor.fetchall()
    updated_count = 0
    
    for user_id, pw in users:
        if pw and not pw.startswith("$2"): 
            hashed_pw = pwd_context.hash(pw)
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
            updated_count += 1
            
    conn.commit()
    print(f"Passwords hashed successfully. Updated {updated_count} user(s).")
    conn.close()

if __name__ == "__main__":
    migrate()
