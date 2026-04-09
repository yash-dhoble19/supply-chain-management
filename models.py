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
    supplier_code = Column(String, unique=True, index=True, nullable=True)
    company_name = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    contact_email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # --- Updated Fields for Dashboard Compatibility ---
    category = Column(String, default="General")
    product_name = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    reliability_score = Column(Float, default=95.0)  # Legacy compatibility
    reliability_percent = Column(Float, nullable=True)
    on_time_delivery_percent = Column(Float, nullable=True)
    supplier_score = Column(Float, nullable=True)
    delivery_speed_days = Column(Integer, default=5)
    average_delivery_days = Column(Integer, nullable=True)
    lead_time_days = Column(Integer, default=5) # Alias for compatibility
    price_per_unit = Column(Float, default=0.0) # Added for quick cost calc
    unit_price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    delivery_cost = Column(Float, default=0.0)
    minimum_order_quantity = Column(Integer, nullable=True)

    supplier_type = Column(String, default="Strategic")
    status = Column(String, default="ACTIVE")
    preferred_supplier = Column(Boolean, default=False)

    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)

    gst_number = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    # --- Procurement Automation Fields ---
    source = Column(String, default="INTERNAL")  # INTERNAL, ALIBABA, TRADEKEY, GOOGLE_MAPS, MANUAL
    source_url = Column(String, nullable=True)
    source_scraped_at = Column(DateTime(timezone=True), nullable=True)
    responsiveness_flag = Column(String, default="NORMAL")  # NORMAL, SLOW, LOW, UNRESPONSIVE
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    last_response_time_hours = Column(Float, nullable=True)
    total_inquiries_sent = Column(Integer, default=0)
    total_replies_received = Column(Integer, default=0)

    # --- n8n Workflow Compatibility Fields ---
    supplier_id = Column(Integer, nullable=True)  # Mirrors 'id' for n8n queries
    contact_name = Column(String, nullable=True)  # n8n reads this (alias for contact_person)
    last_reply_at = Column(DateTime(timezone=True), nullable=True)
    latest_quote_price = Column(Float, nullable=True)
    latest_quote_delivery = Column(String, nullable=True)
    responsiveness_status = Column(String, default="normal")
    last_escalation_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="supplier"
    )
    email_interactions = relationship(
        "EmailInteraction",
        back_populates="supplier"
    )
    quotes = relationship(
        "SupplierQuote",
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
    tracking_id = Column(String, unique=True, index=True, nullable=True)
    
    # Route Details
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    waypoints = Column(Text, nullable=True) # JSON string of waypoints
    route_geometry = Column(Text, nullable=True) # Polyline string
    total_distance_km = Column(Float, default=0.0)
    distance_km = Column(Float, default=0.0)
    
    # Origin coordinates (stored at creation, never updated)
    origin_lat = Column(Float, nullable=True)
    origin_lon = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    origin_snapped = Column(Boolean, default=False)
    
    # Execution
    status = Column(String, default="CREATED") # CREATED, IN_TRANSIT, DELIVERED
    current_location_lat = Column(Float, nullable=True)
    current_location_lon = Column(Float, nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    progress_percent = Column(Float, default=0.0)
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    load_type = Column(String, default="STANDARD")
    average_speed_kmh = Column(Float, default=50.0)
    fuel_consumption_rate = Column(Float, default=0.28)
    fuel_required_liters = Column(Float, default=0.0)
    route_duration_seconds = Column(Float, default=0.0)
    
    # Dates
    scheduled_date = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Assignments
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    carrier = relationship("Carrier", back_populates="shipments")
    driver = relationship("Driver", back_populates="shipments")
    tracking_logs = relationship(
        "TrackingLog",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="TrackingLog.timestamp"
    )


class TrackingLog(Base):
    __tablename__ = "tracking"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    shipment = relationship("Shipment", back_populates="tracking_logs")

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


# =====================================================
# 11. PROCUREMENT SESSIONS (Sourcing Workflows)
# =====================================================
class ProcurementSession(Base):
    __tablename__ = 'procurement_sessions'

    id = Column(Integer, primary_key=True, index=True)
    session_code = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, nullable=False)
    product_category = Column(String, nullable=True)
    search_query = Column(Text, nullable=True)
    source_types = Column(String, nullable=True)
    status = Column(String, default='ACTIVE')

    total_suppliers_found = Column(Integer, default=0)
    total_inquiries_sent = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    total_quotes = Column(Integer, default=0)
    approved_supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    email_interactions = relationship('EmailInteraction', back_populates='session')
    quotes = relationship('SupplierQuote', back_populates='session')


# =====================================================
# 12. EMAIL INTERACTIONS (Communication Tracking)
# =====================================================
class EmailInteraction(Base):
    __tablename__ = 'email_interactions'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('procurement_sessions.id'), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False, index=True)
    product_name = Column(String, nullable=True)
    quantity_requested = Column(Integer, nullable=True)
    specs = Column(Text, nullable=True)

    status = Column(String, nullable=False, default='inquiry_pending')

    # --- n8n-compatible column names ---
    message_id = Column(String, nullable=True)        # Gmail message ID
    thread_id = Column(String, nullable=True, index=True)  # Gmail thread ID
    subject = Column(Text, nullable=True)              # Email subject
    body = Column(Text, nullable=True)                 # Email body
    email_type = Column(String, nullable=True)         # inquiry, reply, follow_up
    recipient_email = Column(String, nullable=True)
    sender_email = Column(String, nullable=True)
    inquiry_details = Column(Text, nullable=True)      # JSON of inquiry params
    extracted_data = Column(Text, nullable=True)       # JSON of AI-extracted quote

    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)  # When reply arrived
    follow_up_sent_at = Column(DateTime(timezone=True), nullable=True)

    # --- Dashboard-specific fields ---
    followup_count = Column(Integer, default=0)
    max_followups = Column(Integer, default=2)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session = relationship('ProcurementSession', back_populates='email_interactions')
    supplier = relationship('Supplier', back_populates='email_interactions')
    quote = relationship('SupplierQuote', back_populates='interaction', uselist=False)
    logs = relationship('EmailInteractionLog', back_populates='interaction',
                        cascade='all, delete-orphan', order_by='EmailInteractionLog.created_at')


# =====================================================
# 13. SUPPLIER QUOTES (Extracted Quote Data)
# =====================================================
class SupplierQuote(Base):
    __tablename__ = 'supplier_quotes'

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey('email_interactions.id'), nullable=True, unique=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('procurement_sessions.id'), nullable=True, index=True)

    unit_price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    minimum_order_qty = Column(Integer, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    payment_terms = Column(String, nullable=True)
    validity_days = Column(Integer, nullable=True)

    total_quoted_amount = Column(Float, nullable=True)
    discount_offered = Column(Float, nullable=True)
    delivery_terms = Column(String, nullable=True)

    notes = Column(Text, nullable=True)
    raw_email_text = Column(Text, nullable=True)
    ai_extraction_confidence = Column(Float, default=100.0)

    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    interaction = relationship('EmailInteraction', back_populates='quote')
    supplier = relationship('Supplier', back_populates='quotes')
    session = relationship('ProcurementSession', back_populates='quotes')


# =====================================================
# 14. EMAIL INTERACTION LOGS (Timeline)
# =====================================================
class EmailInteractionLog(Base):
    __tablename__ = 'email_interaction_logs'

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey('email_interactions.id'), nullable=False, index=True)
    
    event_type = Column(String, nullable=False) # e.g. INQUIRY_TRIGGERED, INQUIRY_SENT, FOLLOW_UP_1, REPLY_RECEIVED, QUOTE_EXTRACTED
    event_data = Column(Text, nullable=True)    # JSON structured data

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    interaction = relationship('EmailInteraction', back_populates='logs')

# =====================================================
# 13. MANUFACTURING GOODS (Production Tracking)
# =====================================================
class ManufacturingGoods(Base):
    __tablename__ = "manufacturing_goods"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, nullable=False)
    status = Column(String, default="Pending")
    progress = Column(Integer, default=0)  # 0-100
    start_date = Column(Date, nullable=True)
    est_completion = Column(Date, nullable=True)
    unit_price = Column(Float, nullable=False)

# =====================================================
# 14. PUBLISHED GOODS (Marketplace)
# =====================================================
class PublishedGoods(Base):
    __tablename__ = "published_goods"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    image_url = Column(Text, nullable=True)
    supplier_name = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Optionally, link to product
    product = relationship("Product")

# =====================================================
# 15. LOGISTICS ORDERS (For Logistics Dashboard)
# =====================================================
class LogisticsOrder(Base):
    __tablename__ = "logistics_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=True)  # Link to sales order (nullable for now)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    status = Column(String, default="Pending")  # Will be updated to 'In Progress' when accepted by driver
    driver_id = Column(Integer, nullable=True)  # Ensure this is present for assignment
    current_location_lat = Column(Float, nullable=True)
    current_location_lon = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    retailer_name = Column(String, nullable=True)
    retailer_email = Column(String, nullable=True)
    retailer_phone = Column(String, nullable=True)
    retailer_location = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    category = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    imageUrl = Column(Text, nullable=True)
    supplierName = Column(String, nullable=True)
    publishedAt = Column(String, nullable=True)


# =====================================================
# 16. SCHEDULE REQUESTS (Manufacturer → Driver Workflow)
# =====================================================
class ScheduleRequest(Base):
    __tablename__ = "schedule_requests"

    id = Column(Integer, primary_key=True, index=True)

    # Shipment info
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    load_type = Column(String, default="STANDARD")
    distance_km = Column(Float, nullable=True)
    eta_hours = Column(Float, nullable=True)

    # Driver assignment
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    driver_name = Column(String, nullable=True)

    # Product info
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

    # Carrier type
    carrier_type = Column(String, nullable=True)

    # Status: PENDING → ACCEPTED / REJECTED → IN_PROGRESS → COMPLETED
    status = Column(String, default="PENDING")

    # Who created the schedule
    manufacturer_name = Column(String, default="ChainMind Manufacturing")

    # Related logistics order (if originated from retailer order)
    logistics_order_id = Column(Integer, nullable=True)
    shipment_id = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    driver = relationship("Driver")

# anything
