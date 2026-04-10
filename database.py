# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required and must point to the Neon PostgreSQL database from .env")

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,           # Keep 10 persistent connections alive
    max_overflow=20,        # Allow up to 20 extra connections during spikes
    pool_recycle=300,       # Recycle connections every 5 minutes
    connect_args={
        "connect_timeout": 10   # 10 second connection timeout
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def initialize_database():
    import models
    from services.logistics_schema import sync_logistics_schema
    from services.supplier_schema import sync_supplier_schema
    from services.procurement_automation_schema import sync_procurement_automation_schema

    models.Base.metadata.create_all(bind=engine)
    sync_supplier_schema(engine)
    sync_logistics_schema(engine)
    sync_procurement_automation_schema(engine)

# Dependency to get DB session in endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# anything
