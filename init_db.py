# init_db.py
from database import engine, SessionLocal
import models
from datetime import datetime, timedelta

# 1. Create the Database Tables
print("🛠️  Creating database tables...")
models.Base.metadata.create_all(bind=engine)

# 2. Start a Session
db = SessionLocal()

def seed_database():
    # Check if data exists
    if db.query(models.Product).first():
        print("⚠️  Database already contains data. Skipping seed.")
        return

    print("🌱 Adding sample data...")

    # --- ADD SUPPLIERS ---
    sup1 = models.Supplier(
        name="Global Steel Co.", 
        contact_email="sales@globalsteel.com", 
        category="Raw Material", 
        lead_time_days=5,
        price_per_unit=45.0,
        reliability_score=9.5
    )
    sup2 = models.Supplier(
        name="TechChip Solutions", 
        contact_email="support@techchip.com", 
        category="Electronics", 
        lead_time_days=14,
        price_per_unit=120.0,
        reliability_score=8.8
    )
    db.add_all([sup1, sup2])
    db.commit() # Commit to get IDs

    # --- ADD PRODUCTS ---
    p1 = models.Product(
        sku="RAW-ST-001", name="Steel Sheets", category="Raw Material", stage="Raw Material",
        current_stock=1200, safety_stock_level=200, optimal_stock_level=1000, unit_price=45.0
    )
    p2 = models.Product(
        sku="ELC-CH-005", name="Microcontroller A1", category="Electronics", stage="Work in Progress",
        current_stock=50, safety_stock_level=100, optimal_stock_level=500, unit_price=120.0
    )
    db.add_all([p1, p2])
    db.commit()

    # --- ADD A PURCHASE ORDER ---
    po = models.PurchaseOrder(
        po_number="PO-2024-001",
        supplier_id=sup1.id,
        product_name="Steel Sheets",
        quantity=500,
        total_value=22500.0,
        status="Pending Approval",
        priority="Medium",
        created_at=datetime.utcnow()
    )
    db.add(po)
    db.commit()

    print("✅ Success! 'scm.db' created with sample data.")

if __name__ == "__main__":
    seed_database()
    db.close()
# anything
