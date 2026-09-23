from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, unique=True)
  email = Column(String, unique=True)
  hashed_password = Column(String)
  
class PredictionRecord(Base):
  __tablename__ = "prediction_record"
  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(ForeignKey("users.id")) 
  k_eff= Column(Float)
  reactor_status= Column(String)
  uncertainty=Column(Float)
  enrichment_percent=Column(Float)
  fuel_density=Column(Float)
  moderator_density=Column(Float)
  created_at = Column(DateTime, default=datetime.utcnow)
