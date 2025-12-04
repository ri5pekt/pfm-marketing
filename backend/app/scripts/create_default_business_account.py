import sys
from app.core.db import SessionLocal
from app.features.meta_campaigns.models import BusinessAccount

def create_default_business_account():
    db = SessionLocal()
    try:
        # Check if default account already exists
        existing = db.query(BusinessAccount).filter(BusinessAccount.is_default == True).first()
        if existing:
            print(f"Default business account '{existing.name}' already exists")
            return

        # Check if "Particle Supplements" exists
        particle = db.query(BusinessAccount).filter(BusinessAccount.name == "Particle Supplements").first()
        if particle:
            # Set it as default
            particle.is_default = True
            db.commit()
            print(f"Set '{particle.name}' as default business account")
            return

        # Create new default account
        account = BusinessAccount(
            name="Particle Supplements",
            description="Default business account for Particle Supplements",
            is_default=True
        )
        db.add(account)
        db.commit()
        print(f"Created default business account: {account.name}")
    finally:
        db.close()

if __name__ == "__main__":
    create_default_business_account()

