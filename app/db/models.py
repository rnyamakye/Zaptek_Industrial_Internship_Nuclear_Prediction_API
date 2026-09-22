from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # stored as a bcrypt hash
    role = Column(String, default="user", nullable=False)  # "user" or "admin"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# NOTE: Predictions table lives in this same file once Reginald adds it,
# so it shares Base/metadata with User for create_all() and FKs to user_id.