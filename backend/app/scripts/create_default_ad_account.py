import sys
from app.core.db import SessionLocal
from app.features.meta_campaigns.models import AdAccount

def create_default_ad_account():
    db = SessionLocal()
    try:
        # Check if default account already exists
        existing = db.query(AdAccount).filter(AdAccount.is_default == True).first()
        if existing:
            print(f"Default ad account '{existing.name}' already exists")
            return

        # Check if "Particle Supplements" exists
        particle = db.query(AdAccount).filter(AdAccount.name == "Particle Supplements").first()
        if particle:
            # Set it as default
            particle.is_default = True
            db.commit()
            print(f"Set '{particle.name}' as default ad account")
            return

        # Create new default account
        account = AdAccount(
            name="Particle Supplements",
            description="Default ad account for Particle Supplements",
            is_default=True
        )
        db.add(account)
        db.commit()
        print(f"Created default ad account: {account.name}")
    finally:
        db.close()

if __name__ == "__main__":
    create_default_ad_account()

