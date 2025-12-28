# model.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Date,
    Boolean,
    DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime

# =====================================================
# 1. USERS (Authentication & Roles)
# =====================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # ADMIN, MANAGER, LOGISTICS


# =====================================================
# 2. PRODUCTS (Core Inventory Entity)
# =====================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    category = Column(String, nullable=False)
    stage = Column(
        String,
        default="Raw Material"
    )  # Raw Material → Work in Progress → Finished

    # Stock & Costing
    current_stock = Column(Integer, default=0)
    safety_stock_level = Column(Integer, default=10)
    optimal_stock_level = Column(Integer, default=50)
    unit_price = Column(Float, nullable=False)

    # Relationships
    inventory_logs = relationship(
        "InventoryLog",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    forecasts = relationship(
        "Forecast",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    po_items = relationship(
        "POItem",
        back_populates="product"
    )


# =====================================================
# 3. INVENTORY LOGS (Stock Movement History)
# =====================================================
class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    change_date = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )
    quantity_change = Column(Integer, nullable=False)  # +ve / -ve
    reason = Column(
        String,
        nullable=False
    )  # SALE, PO_RECEIVED, DAMAGE, ADJUSTMENT

    stockout_flag = Column(Boolean, default=False)

    product = relationship("Product", back_populates="inventory_logs")


# =====================================================
# 4. FORECASTS (AI / ML Demand Predictions)
# =====================================================
class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    forecast_date = Column(Date, nullable=False)
    predicted_quantity = Column(Float, nullable=False)
    confidence_score = Column(Float)  # 0–1 or %

    product = relationship("Product", back_populates="forecasts")


# =====================================================
# 5. ORDERS (Sales / Delivery)
# =====================================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    delivery_address = Column(String, nullable=True)

    status = Column(
        String,
        default="PENDING"
    )  # PENDING → CONFIRMED → SHIPPED → DELIVERED

    ai_risk_assessment = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# =====================================================
# 6. SUPPLIERS (Procurement)
# =====================================================
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    contact_email = Column(String, nullable=False)

    reliability_score = Column(Float)  # 1–10 scale
    delivery_speed_days = Column(Integer)

    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier"
    )


# =====================================================
# 7. PURCHASE ORDERS (Inbound Supply)
# =====================================================
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True, nullable=False)

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False
    )

    total_amount = Column(DECIMAL(10, 2))
    status = Column(
        String,
        default="DRAFT"
    )  # DRAFT → APPROVED → IN_TRANSIT → RECEIVED

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    expected_delivery_date = Column(Date)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship(
        "POItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )


# =====================================================
# 8. PURCHASE ORDER ITEMS
# =====================================================
class POItem(Base):
    __tablename__ = "po_items"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(
        Integer,
        ForeignKey("purchase_orders.id"),
        nullable=False
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity_ordered = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="po_items")
