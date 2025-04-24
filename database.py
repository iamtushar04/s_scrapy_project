from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker

# Path to your existing SQLite DB
DATABASE_URL = "sqlite:///./sourav.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()
metadata.reflect(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
