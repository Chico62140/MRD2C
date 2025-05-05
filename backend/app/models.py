from sqlalchemy import Column, Integer, String
from .database import Base

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    path = Column(String)
    filename = Column(String)
    description = Column(String)
    status = Column(String, default="pending")
