import sys
import argparse
from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.auth.models import User

def create_user(email: str, password: str, is_admin: bool = False):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists")
            return

        # Create new user
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_admin=is_admin,
            is_active=True
        )
        db.add(user)
        db.commit()
        print(f"User {email} created successfully (admin: {is_admin})")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--admin", action="store_true", help="Make user an admin")

    args = parser.parse_args()
    create_user(args.email, args.password, args.admin)

