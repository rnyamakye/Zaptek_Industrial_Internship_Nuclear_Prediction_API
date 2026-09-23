from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # stored as a bcrypt hash
    role = Column(String, default="user", nullable=False)  # "user" or "admin"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PredictionRecord(Base):
    __tablename__ = "prediction_record"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"))
    k_eff = Column(Float)
    reactor_status = Column(String)
    uncertainty = Column(Float)
    enrichment_percent = Column(Float)
    fuel_density = Column(Float)
    moderator_density = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
