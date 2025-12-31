"""Link federated accounts to existing users"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import engine
from app.database.models import FederatedIdentity, User


def link_accounts():
    with Session(engine) as session:
        # Get superuser
        superuser = session.execute(
            select(User).where(User.email == "skakumanu@gmail.com")
        ).scalar_one_or_none()

        if superuser:
            # Check if already linked
            existing = session.execute(
                select(FederatedIdentity).where(
                    FederatedIdentity.user_id == superuser.id,
                    FederatedIdentity.provider == "google",
                )
            ).scalar_one_or_none()

            if not existing:
                google_fed = FederatedIdentity(
                    id=str(uuid.uuid4()),
                    user_id=superuser.id,
                    provider="google",
                    provider_user_id=f"google_{superuser.email}",
                    email=superuser.email,
                )
                session.add(google_fed)
                print(f"✓ Linked {superuser.email} to Google federated auth")
            else:
                print(f"✓ {superuser.email} already linked to Google")
        else:
            print("⚠ Superuser skakumanu@gmail.com not found")

        # Get admin user
        admin = session.execute(
            select(User).where(User.email == "skakumanu@hotmail.com")
        ).scalar_one_or_none()

        if admin:
            # Check if already linked
            existing = session.execute(
                select(FederatedIdentity).where(
                    FederatedIdentity.user_id == admin.id,
                    FederatedIdentity.provider == "microsoft",
                )
            ).scalar_one_or_none()

            if not existing:
                microsoft_fed = FederatedIdentity(
                    id=str(uuid.uuid4()),
                    user_id=admin.id,
                    provider="microsoft",
                    provider_user_id=f"microsoft_{admin.email}",
                    email=admin.email,
                )
                session.add(microsoft_fed)
                print(f"✓ Linked {admin.email} to Microsoft federated auth")
            else:
                print(f"✓ {admin.email} already linked to Microsoft")
        else:
            print("⚠ Admin user skakumanu@hotmail.com not found")

        session.commit()
        print("\n✅ Federated account linking complete!")


if __name__ == "__main__":
    link_accounts()
