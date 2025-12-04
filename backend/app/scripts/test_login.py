"""Test login credentials"""
from app.core.db import SessionLocal
from app.core.security import verify_password
from app.auth.models import User

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == 'admin@example.com').first()
    if user:
        print(f"User found: {user.email}")
        print(f"Is admin: {user.is_admin}")
        print(f"Is active: {user.is_active}")
        test_password = verify_password('admin123', user.hashed_password)
        print(f"Password 'admin123' verification: {test_password}")
    else:
        print("User not found!")
finally:
    db.close()

