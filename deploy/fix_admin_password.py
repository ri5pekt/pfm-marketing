#!/usr/bin/env python3
"""Fix admin user password"""
import sys
sys.path.insert(0, '/app')

from app.core.db import SessionLocal
from app.auth.models import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == 'admin@pfm-qa.com').first()
    if user:
        user.hashed_password = get_password_hash('ChangeMe123!')
        db.commit()
        print('Password updated successfully!')
        print('Email: admin@pfm-qa.com')
        print('Password: ChangeMe123!')
    else:
        print('User not found')
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
    sys.exit(1)
finally:
    db.close()

