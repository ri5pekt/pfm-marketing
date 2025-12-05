#!/usr/bin/env python3
"""Create admin user directly in database"""
import sys
sys.path.insert(0, '/app')

from app.core.db import SessionLocal
from app.auth.models import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    # Check if user exists
    existing = db.query(User).filter(User.email == 'admin@pfm-qa.com').first()
    if existing:
        print('User admin@pfm-qa.com already exists')
        sys.exit(0)

    # Create user
    user = User(
        email='admin@pfm-qa.com',
        hashed_password=get_password_hash('ChangeMe123!'),
        is_admin=True
    )
    db.add(user)
    db.commit()
    print('User admin@pfm-qa.com created successfully with password: ChangeMe123!')
    print('PLEASE CHANGE THIS PASSWORD AFTER FIRST LOGIN!')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
    sys.exit(1)
finally:
    db.close()

