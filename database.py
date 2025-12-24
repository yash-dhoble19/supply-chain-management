from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ⚠️ REPLACE 'password' with your actual PostgreSQL password
# Format: postgresql://username:password@localhost/dbname
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:yash123@localhost/supply_chain_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session in endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()