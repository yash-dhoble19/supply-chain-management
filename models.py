# models.py
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

    # --- Updated Fields for Dashboard Compatibility ---
    category = Column(String, default="General")
    reliability_score = Column(Float, default=95.0)  # 1–10 scale
    delivery_speed_days = Column(Integer, default=5)
    lead_time_days = Column(Integer, default=5) # Alias for compatibility
    price_per_unit = Column(Float, default=0.0) # Added for quick cost calc
    delivery_cost = Column(Float, default=0.0)

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

    # --- Updated Fields for Dashboard Compatibility ---
    product_name = Column(String, nullable=True) # Snapshot for simple display
    quantity = Column(Integer, nullable=True)
    total_value = Column(Float, default=0.0)
    priority = Column(String, default="Medium")

    total_amount = Column(DECIMAL(10, 2), nullable=True) # Kept original field
    status = Column(
        String,
        default="DRAFT"
    )  # DRAFT → APPROVED → IN_TRANSIT → RECEIVED

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    expected_delivery = Column(DateTime, nullable=True)
    expected_delivery_date = Column(Date, nullable=True)

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


# =====================================================
# 9. LOGISTICS MANAGEMENT (New Features)
# =====================================================

class Carrier(Base):
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    contact_info = Column(String, nullable=True)
    fleet_size = Column(Integer, default=0)
    rating = Column(Float, default=4.5)
    
    drivers = relationship("Driver", back_populates="carrier", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="carrier")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    license_number = Column(String, unique=True, nullable=False)
    status = Column(String, default="AVAILABLE") # AVAILABLE, ON_TRIP, OFF_DUTY
    
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=False)
    carrier = relationship("Carrier", back_populates="drivers")
    
    shipments = relationship("Shipment", back_populates="driver")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True, nullable=False)
    
    # Route Details
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    waypoints = Column(Text, nullable=True) # JSON string of waypoints
    route_geometry = Column(Text, nullable=True) # Polyline string
    total_distance_km = Column(Float, default=0.0)
    
    # Origin coordinates (stored at creation, never updated)
    origin_lat = Column(Float, nullable=True)
    origin_lon = Column(Float, nullable=True)
    origin_snapped = Column(Boolean, default=False)
    
    # Execution
    status = Column(String, default="SCHEDULED") # SCHEDULED, IN_TRANSIT, DELIVERED, DELAYED
    current_location_lat = Column(Float, nullable=True)
    current_location_lon = Column(Float, nullable=True)
    progress_percent = Column(Float, default=0.0)
    
    # Dates
    scheduled_date = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Assignments
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    carrier = relationship("Carrier", back_populates="shipments")
    driver = relationship("Driver", back_populates="shipments")

# =====================================================
# 10. AI INSIGHTS (Stored Intelligence)
# =====================================================
class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, index=True, nullable=False) # e.g. "FORECAST", "ORDER"
    entity_id = Column(String, index=True, nullable=False)   # ID of the related record
    insight_type = Column(String, nullable=False)            # e.g. "RISK", "SUMMARY"
    
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())