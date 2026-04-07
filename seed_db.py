"""
Database Seed Script for Supply Chain Management System
Run this to populate the database with realistic sample data
"""

import requests
import random
from datetime import datetime, timedelta

API_URL = "http://127.0.0.1:8000"

# === Sample Data ===

SAMPLE_SUPPLIERS = [
    {
        "name": "Global Tech Suppliers",
        "contact_email": "procurement@globaltech.com",
        "category": "Electronics",
        "reliability_score": 95.0,
        "delivery_speed_days": 3,
        "price_per_unit": 15.50
    },
    {
        "name": "Premium Fabrics Inc.",
        "contact_email": "orders@premiumfabrics.com",
        "category": "Raw Material",
        "reliability_score": 92.0,
        "delivery_speed_days": 5,
        "price_per_unit": 8.75
    },
    {
        "name": "FastTrack Logistics",
        "contact_email": "supply@fasttrack.com",
        "category": "Electronics",
        "reliability_score": 88.0,
        "delivery_speed_days": 2,
        "price_per_unit": 18.00
    },
    {
        "name": "EcoFriendly Materials Co.",
        "contact_email": "sales@ecofriendly.com",
        "category": "Raw Material",
        "reliability_score": 90.0,
        "delivery_speed_days": 7,
        "price_per_unit": 12.25
    },
    {
        "name": "Quality Apparel Supply",
        "contact_email": "orders@qualityapparel.com",
        "category": "Apparel",
        "reliability_score": 85.0,
        "delivery_speed_days": 6,
        "price_per_unit": 10.50
    },
    {
        "name": "Home Goods Wholesale",
        "contact_email": "wholesale@homegoods.com",
        "category": "Home",
        "reliability_score": 87.0,
        "delivery_speed_days": 5,
        "price_per_unit": 14.00
    }
]

SAMPLE_PRODUCTS = [
    # Critical Items (Low Stock)
    {
        "sku": "ELEC-001",
        "name": "Microcontroller Chips",
        "category": "Electronics",
        "stage": "Raw Material",
        "current_stock": 50,
        "safety_stock_level": 100,
        "optimal_stock_level": 500,
        "unit_price": 15.50
    },
    {
        "sku": "FAB-001",
        "name": "Gore-Tex Fabric Sheets",
        "category": "Raw Material",
        "stage": "Raw Material",
        "current_stock": 80,
        "safety_stock_level": 150,
        "optimal_stock_level": 800,
        "unit_price": 8.75
    },
    {
        "sku": "ELEC-002",
        "name": "LCD Display Panels",
        "category": "Electronics",
        "stage": "Raw Material",
        "current_stock": 45,
        "safety_stock_level": 80,
        "optimal_stock_level": 400,
        "unit_price": 22.00
    },
    
    # Medium Stock Items
    {
        "sku": "APP-001",
        "name": "Cotton T-Shirt Blanks",
        "category": "Apparel",
        "stage": "Work in Progress",
        "current_stock": 350,
        "safety_stock_level": 200,
        "optimal_stock_level": 600,
        "unit_price": 5.50
    },
    {
        "sku": "HOME-001",
        "name": "Ceramic Dinner Plates",
        "category": "Home",
        "stage": "Finished",
        "current_stock": 280,
        "safety_stock_level": 150,
        "optimal_stock_level": 500,
        "unit_price": 12.00
    },
    {
        "sku": "ELEC-003",
        "name": "Lithium Battery Cells",
        "category": "Electronics",
        "stage": "Raw Material",
        "current_stock": 220,
        "safety_stock_level": 180,
        "optimal_stock_level": 600,
        "unit_price": 18.50
    },
    
    # High Stock Items
    {
        "sku": "FAB-002",
        "name": "Polyester Fabric Rolls",
        "category": "Raw Material",
        "stage": "Raw Material",
        "current_stock": 850,
        "safety_stock_level": 200,
        "optimal_stock_level": 600,
        "unit_price": 6.25
    },
    {
        "sku": "APP-002",
        "name": "Denim Jeans",
        "category": "Apparel",
        "stage": "Finished",
        "current_stock": 480,
        "safety_stock_level": 100,
        "optimal_stock_level": 400,
        "unit_price": 28.00
    },
    {
        "sku": "HOME-002",
        "name": "Glass Coffee Mugs",
        "category": "Home",
        "stage": "Finished",
        "current_stock": 420,
        "safety_stock_level": 150,
        "optimal_stock_level": 400,
        "unit_price": 8.50
    },
    {
        "sku": "ELEC-004",
        "name": "USB-C Cables",
        "category": "Electronics",
        "stage": "Finished",
        "current_stock": 680,
        "safety_stock_level": 200,
        "optimal_stock_level": 600,
        "unit_price": 4.50
    },
    
    # Additional Critical Items
    {
        "sku": "RAW-001",
        "name": "Steel Sheets",
        "category": "Raw Material",
        "stage": "Raw Material",
        "current_stock": 35,
        "safety_stock_level": 100,
        "optimal_stock_level": 500,
        "unit_price": 45.00
    },
    {
        "sku": "APP-003",
        "name": "Leather Jackets",
        "category": "Apparel",
        "stage": "Finished",
        "current_stock": 25,
        "safety_stock_level": 50,
        "optimal_stock_level": 200,
        "unit_price": 120.00
    }
]

def seed_database():
    """Main seeding function"""
    print("🌱 Starting Database Seed...")
    print("=" * 50)
    
    # 1. Seed Suppliers
    print("\n📦 Seeding Suppliers...")
    supplier_ids = {}
    
    for supplier in SAMPLE_SUPPLIERS:
        try:
            response = requests.post(
                f"{API_URL}/api/procurement/suppliers",
                json={
                    "supplier_name": supplier["name"],
                    "email": supplier["contact_email"],
                    "company_name": supplier["name"],
                    "product_category": supplier["category"],
                    "unit_price": supplier["price_per_unit"],
                    "average_delivery_days": supplier["delivery_speed_days"],
                    "reliability_percent": supplier["reliability_score"],
                    "on_time_delivery_percent": max(supplier["reliability_score"] - 2, 0),
                    "currency": "USD",
                    "delivery_cost": 0,
                    "supplier_type": "Strategic",
                    "status": "ACTIVE",
                    "preferred_supplier": False
                }
            )
            if response.status_code == 200:
                result = response.json()
                supplier_record = result.get("supplier") or {}
                supplier_ids[supplier['name']] = int(supplier_record.get("supplier_id", 0))
                print(f"  ✅ Added: {supplier['name']} (Trust Score: {supplier_record.get('supplier_score', 'n/a')})")
            else:
                print(f"  ⚠️ Skipped: {supplier['name']} (Already exists or error)")
        except Exception as e:
            print(f"  ❌ Error adding {supplier['name']}: {e}")
    
    # 2. Seed Products
    print("\n📦 Seeding Products...")
    product_ids = {}
    
    for product in SAMPLE_PRODUCTS:
        try:
            response = requests.post(
                f"{API_URL}/products/",
                json=product
            )
            if response.status_code == 200:
                result = response.json()
                product_ids[product['sku']] = result['id']
                
                # Determine status for display
                stock_pct = (product['current_stock'] / product['optimal_stock_level']) * 100
                if stock_pct < 20:
                    status = "🚨 CRITICAL"
                elif stock_pct < 50:
                    status = "⚠️ LOW"
                else:
                    status = "✅ OK"
                
                print(f"  {status} Added: {product['name']} ({product['current_stock']}/{product['optimal_stock_level']} units)")
            else:
                print(f"  ⚠️ Skipped: {product['name']} (Already exists)")
        except Exception as e:
            print(f"  ❌ Error adding {product['name']}: {e}")
    
    # 3. Create Sample Purchase Orders
    print("\n📄 Creating Sample Purchase Orders...")
    
    # Create 3 sample POs in different statuses
    sample_pos = [
        {
            "product_sku": "ELEC-001",
            "supplier": "Global Tech Suppliers",
            "quantity": 500,
            "priority": "Urgent",
            "status_target": "APPROVED"
        },
        {
            "product_sku": "FAB-001",
            "supplier": "Premium Fabrics Inc.",
            "quantity": 700,
            "priority": "High",
            "status_target": "IN_TRANSIT"
        },
        {
            "product_sku": "RAW-001",
            "supplier": "EcoFriendly Materials Co.",
            "quantity": 400,
            "priority": "Urgent",
            "status_target": "DRAFT"
        }
    ]
    
    for po_data in sample_pos:
        product_sku = po_data['product_sku']
        supplier_name = po_data['supplier']
        
        if product_sku not in product_ids or supplier_name not in supplier_ids:
            print(f"  ⚠️ Skipping PO for {product_sku} - Missing data")
            continue
        
        try:
            # Find product details
            product = next(p for p in SAMPLE_PRODUCTS if p['sku'] == product_sku)
            
            # Create PO
            po_payload = {
                "supplier_id": supplier_ids[supplier_name],
                "product_id": product_ids[product_sku],
                "product_name": product['name'],
                "quantity": po_data['quantity'],
                "unit_price": product['unit_price'],
                "priority": po_data['priority']
            }
            
            response = requests.post(
                f"{API_URL}/procurement/po/create",
                json=po_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                po_number = result['po_number']
                po_id = result['po_id']
                
                # Update status if not DRAFT
                if po_data['status_target'] != "DRAFT":
                    requests.put(
                        f"{API_URL}/procurement/po/{po_id}/status",
                        params={"status": po_data['status_target']}
                    )
                
                print(f"  ✅ Created: {po_number} | {product['name']} | Status: {po_data['status_target']}")
            else:
                print(f"  ❌ Failed to create PO for {product_sku}")
        except Exception as e:
            print(f"  ❌ Error creating PO for {product_sku}: {e}")
    
    # 4. Create Sample Inventory Logs
    print("\n📝 Creating Sample Inventory Logs...")
    
    sample_logs = [
        {"product_sku": "ELEC-001", "change": -30, "reason": "Emergency Production Run"},
        {"product_sku": "FAB-001", "change": -50, "reason": "Large Customer Order"},
        {"product_sku": "APP-001", "change": 100, "reason": "Supplier Delivery"},
        {"product_sku": "RAW-001", "change": -15, "reason": "Damaged During Handling"}
    ]
    
    for log in sample_logs:
        if log['product_sku'] in product_ids:
            try:
                response = requests.post(
                    f"{API_URL}/inventory/logs",
                    json={
                        "product_id": product_ids[log['product_sku']],
                        "quantity_change": log['change'],
                        "reason": log['reason']
                    }
                )
                if response.status_code == 200:
                    print(f"  ✅ Logged: {log['product_sku']} ({log['change']:+d} units) - {log['reason']}")
            except Exception as e:
                print(f"  ❌ Error logging for {log['product_sku']}: {e}")
    
    # 5. Summary
    print("\n" + "=" * 50)
    print("🎉 Database Seeding Complete!")
    print("=" * 50)
    print(f"\n📊 Summary:")
    print(f"  • Suppliers Added: {len(supplier_ids)}/{len(SAMPLE_SUPPLIERS)}")
    print(f"  • Products Added: {len(product_ids)}/{len(SAMPLE_PRODUCTS)}")
    print(f"  • Purchase Orders Created: {len(sample_pos)}")
    print(f"  • Inventory Logs Created: {len(sample_logs)}")
    
    print(f"\n🚀 You can now:")
    print(f"  1. View the Dashboard at: http://localhost:8501")
    print(f"  2. Check Procurement recommendations")
    print(f"  3. Manage suppliers and create POs")
    print(f"  4. Monitor inventory health scores")
    
    print(f"\n💡 Pro Tip: Check the Procurement Agent page to see AI recommendations!")

if __name__ == "__main__":
    try:
        # Test connection first
        print("🔍 Testing API connection...")
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            print("✅ API is online!\n")
            seed_database()
        else:
            print("❌ API returned unexpected status code")
            print("💡 Make sure your backend is running: python -m uvicorn main:app --reload")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API!")
        print("💡 Please start your backend first:")
        print("   python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
