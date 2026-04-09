from database import engine, SessionLocal
import models
from sqlalchemy import text

def force_update_schema():
    print("🛠️ Force updating schema for logistics tables...")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Drop table if exists
        print("dropping shipments table...")
        # Use raw SQL to drop table to avoid dependency issues if possible or just use metadata
        # models.Base.metadata.drop_all(bind=engine, tables=[models.Shipment.__table__])
        # Force drop cascade
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS shipments CASCADE"))
            conn.commit()
            print("✅ Dropped table 'shipments'")
            
        # Recreate tables
        print("Recreating tables...")
        models.Base.metadata.create_all(bind=engine)
        print("✅ Schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    force_update_schema()

# anything
