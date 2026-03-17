from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./water_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# CHECK THIS LINE CAREFULLY:
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class WaterLog(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    tds = Column(Float)
    ph = Column(Float)
    turbidity = Column(Float)
    flow = Column(Float)
    temp = Column(Float)
    uv_status = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    gps_active = Column(Boolean)
    health = Column(String)

Base.metadata.create_all(bind=engine)