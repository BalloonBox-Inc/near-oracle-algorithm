from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from os import getenv
load_dotenv()


DATABASE_URL = getenv('DATABASE_URL')
if 'postgresql' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgres', 'postgresql')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# create database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
