import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./digitalfarm.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# ✅ SAVE PREDICTION FUNCTION (ONLY HERE)
import sqlite3

conn = sqlite3.connect("digitalfarm.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dose_mg REAL,
    treatment_days REAL,
    days_after_treatment REAL,
    prediction TEXT
)
""")

conn.commit()