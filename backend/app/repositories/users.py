from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(
    db: Session, *, email: str, full_name: str, password_hash: str
) -> User:
    user = User(email=email, full_name=full_name.strip(), password_hash=password_hash)
    db.add(user)
    db.flush()
    return user
