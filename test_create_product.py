#!/usr/bin/env python3
"""Test script for product creation"""
import requests
import json

BASE_URL = "http://localhost:8000"

product_data = {
    "sku": "TEST-SKU-001",
    "name": "Test Product",
    "category": "Electronics",
    "stage": "WAREHOUSE",
    "current_stock": 10,
    "safety_stock_level": 5,
    "optimal_stock_level": 50,
    "unit_price": 99.99
}

print("Testing product creation...")
print(f"URL: {BASE_URL}/api/products/")
print(f"Payload: {json.dumps(product_data, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/products/",
        json=product_data,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Product created successfully!")
    else:
        print(f"\n❌ Failed to create product")
except Exception as e:
    print(f"\n❌ Error: {e}")
