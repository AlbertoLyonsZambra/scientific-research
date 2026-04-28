from sqlalchemy import Column, Integer, String, Float, Date, Time
from data.database import Base

class Earthquake(Base):
    __tablename__ = "earthquakes"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True)
    location = Column(String(100))
    date = Column(Date)
    centroid_time = Column(Time)
    latitude = Column(Float)
    longitude = Column(Float)
    depth = Column(Float)
    mw = Column(Float)
    mb = Column(Float)
    ms = Column(Float)
