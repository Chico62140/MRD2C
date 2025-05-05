import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Corrected: Use 'postgresql' instead of 'postgres'
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr:1qazXSW2@db:5432/request"
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
