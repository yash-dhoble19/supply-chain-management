from database import engine
from models import Base
from sqlalchemy import text

print("⚠️  WARNING: This will delete all existing data in 'supply_chain_db'.")
confirm = input("Are you sure? (type 'yes' to confirm): ")

if confirm == "yes":
    print("🗑️  Dropping all tables...")
    
    # Connect to the DB and force drop tables
    with engine.connect() as connection:
        # We use CASCADE to remove relationships (orders, inventory, etc.)
        connection.execute(text("DROP TABLE IF EXISTS inventory_logs CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS forecasts CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS po_items CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS purchase_orders CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS orders CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS products CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS suppliers CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        connection.commit()
        
    print("✅ All tables dropped.")
    print("🔄 Now run 'python main.py' to recreate them with the NEW columns.")
else:
    print("❌ Operation cancelled.")
# anything
