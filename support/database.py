from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from os import getenv
load_dotenv()


engine = create_engine(getenv('DATABASE_URL'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# create database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
