from sqlalchemy import create_engine, MetaData, Table,column, inspect
from sqlalchemy.orm import sessionmaker

# Path to your existing SQLite DB
DATABASE_URL = "sqlite:///./sourav.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()
metadata.reflect(bind=engine)
scraped_data = metadata.tables['vorysdata']

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
