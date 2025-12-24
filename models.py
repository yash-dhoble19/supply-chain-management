from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime

# --- 1. USERS (For Authentication) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String) # ADMIN, SCM_MANAGER, INVENTORY_PLANNER, LOGISTICS

# --- 2. PRODUCTS (Inventory) ---
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    name = Column(String)
    current_stock = Column(Integer, default=0)
    safety_stock_level = Column(Integer, default=10)
    
    # Relationship: A product can be in many Purchase Order Items
    po_items = relationship("POItem", back_populates="product")

# --- 3. ORDERS (Sales/Logistics) ---
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    delivery_address = Column(String, nullable=True) # Added this for your Risk Agent
    status = Column(String, default="PENDING")
    ai_risk_assessment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- 4. SUPPLIERS (Procurement) ---
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    contact_email = Column(String)
    reliability_score = Column(Integer) # 1-10
    delivery_speed_days = Column(Integer) # Avg days to deliver
    
    # Relationship: One supplier has many Purchase Orders
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

# --- 5. PURCHASE ORDERS (Pipeline Inventory) ---
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True) # e.g. "PO-2024-001"
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    total_amount = Column(DECIMAL(10, 2))
    status = Column(String, default="DRAFT") # DRAFT, APPROVED, IN_TRANSIT, DELIVERED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expected_delivery_date = Column(Date)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("POItem", back_populates="purchase_order")

# --- 6. PO ITEMS (Items inside a Purchase Order) ---
class POItem(Base):
    __tablename__ = "po_items"
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity_ordered = Column(Integer)
    unit_price = Column(DECIMAL(10, 2))

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="po_items")