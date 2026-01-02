# setup_suppliers.py
# Run this once to populate your database with sample suppliers

from sqlalchemy.orm import Session
import models, database

# Initialize database
models.Base.metadata.create_all(bind=database.engine)
db = database.SessionLocal()

# Sample Suppliers Data
suppliers_data = [
    {
        "name": "TechVendor Global",
        "contact_email": "orders@techvendor.com",
        "category": "Electronics",
        "reliability_score": 96.0,
        "lead_time_days": 8,
        "price_per_unit": 45.50,
        "delivery_cost": 25.0
    },
    {
        "name": "Fashion Wholesale Inc",
        "contact_email": "procurement@fashionwholesale.com",
        "category": "Apparel",
        "reliability_score": 92.0,
        "lead_time_days": 12,
        "price_per_unit": 28.00,
        "delivery_cost": 35.0
    },
    {
        "name": "Organic Foods Distributor",
        "contact_email": "sales@organicfoods.com",
        "category": "Food",
        "reliability_score": 98.0,
        "lead_time_days": 4,
        "price_per_unit": 8.99,
        "delivery_cost": 15.0
    },
    {
        "name": "HomeGoods Supply Co",
        "contact_email": "orders@homegoods.com",
        "category": "Home",
        "reliability_score": 88.0,
        "lead_time_days": 10,
        "price_per_unit": 35.75,
        "delivery_cost": 45.0
    },
    {
        "name": "GreenTech Supplies",
        "contact_email": "info@greentech.com",
        "category": "Electronics",
        "reliability_score": 85.0,
        "lead_time_days": 9,
        "price_per_unit": 42.00,
        "delivery_cost": 30.0
    },
    {
        "name": "Industrial Materials Corp",
        "contact_email": "sales@industrialmaterials.com",
        "category": "Raw Material",
        "reliability_score": 94.0,
        "lead_time_days": 7,
        "price_per_unit": 15.50,
        "delivery_cost": 20.0
    }
]

# Check if suppliers already exist
existing_count = db.query(models.Supplier).count()

if existing_count > 0:
    print(f"⚠️  Database already has {existing_count} suppliers.")
    user_input = input("Do you want to clear and reload? (yes/no): ")
    if user_input.lower() != 'yes':
        print("Setup cancelled.")
        db.close()
        exit()
    
    # Clear existing suppliers
    db.query(models.Supplier).delete()
    db.commit()
    print("✅ Cleared existing suppliers")

# Insert new suppliers
for supplier_data in suppliers_data:
    supplier = models.Supplier(**supplier_data)
    db.add(supplier)

db.commit()
print(f"✅ Successfully added {len(suppliers_data)} suppliers to the database!")

# Verify
suppliers = db.query(models.Supplier).all()
print("\n📋 Suppliers in database:")
for s in suppliers:
    print(f"  - {s.name} ({s.category}) - Lead time: {s.lead_time_days} days")

db.close()
print("\n🎉 Setup complete! You can now run your dashboard.")