from sqlalchemy import text


LOGISTICS_SHIPMENT_COLUMNS = [
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS tracking_id VARCHAR",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS distance_km DOUBLE PRECISION DEFAULT 0",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS origin_lng DOUBLE PRECISION",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS destination_lat DOUBLE PRECISION",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS destination_lng DOUBLE PRECISION",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS current_lat DOUBLE PRECISION",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS current_lng DOUBLE PRECISION",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS progress DOUBLE PRECISION DEFAULT 0",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS started_at TIMESTAMP",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS load_type VARCHAR DEFAULT 'STANDARD'",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS average_speed_kmh DOUBLE PRECISION DEFAULT 50",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS fuel_consumption_rate DOUBLE PRECISION DEFAULT 0.28",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS fuel_required_liters DOUBLE PRECISION DEFAULT 0",
    "ALTER TABLE shipments ADD COLUMN IF NOT EXISTS route_duration_seconds DOUBLE PRECISION DEFAULT 0",
]

LOGISTICS_ORDER_COLUMNS = [
    "ALTER TABLE logistics_orders ADD COLUMN IF NOT EXISTS current_location_lat DOUBLE PRECISION",
    "ALTER TABLE logistics_orders ADD COLUMN IF NOT EXISTS current_location_lon DOUBLE PRECISION",
]


LOGISTICS_INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_shipments_tracking_id_unique ON shipments (tracking_id)",
    "CREATE INDEX IF NOT EXISTS ix_shipments_status ON shipments (status)",
    "CREATE INDEX IF NOT EXISTS ix_tracking_shipment_timestamp ON tracking (shipment_id, timestamp)",
]


BACKFILL_STATEMENTS = [
    """
    UPDATE shipments
    SET tracking_id = COALESCE(tracking_id, tracking_number)
    WHERE tracking_id IS NULL
    """,
    """
    UPDATE shipments
    SET distance_km = COALESCE(distance_km, total_distance_km, 0)
    WHERE distance_km IS NULL OR distance_km = 0
    """,
    """
    UPDATE shipments
    SET origin_lng = COALESCE(origin_lng, origin_lon)
    WHERE origin_lng IS NULL
    """,
    """
    UPDATE shipments
    SET current_lat = COALESCE(current_lat, current_location_lat, origin_lat)
    WHERE current_lat IS NULL
    """,
    """
    UPDATE shipments
    SET current_lng = COALESCE(current_lng, current_location_lon, origin_lon, origin_lng)
    WHERE current_lng IS NULL
    """,
    """
    UPDATE shipments
    SET progress = COALESCE(progress, progress_percent, 0)
    WHERE progress IS NULL
    """,
    """
    UPDATE shipments
    SET status = 'CREATED'
    WHERE status IS NULL OR status IN ('SCHEDULED', 'PENDING')
    """,
]


def sync_logistics_schema(engine) -> None:
    with engine.begin() as connection:
        for statement in LOGISTICS_SHIPMENT_COLUMNS:
            connection.execute(text(statement))

        for statement in LOGISTICS_ORDER_COLUMNS:
            connection.execute(text(statement))

        for statement in BACKFILL_STATEMENTS:
            connection.execute(text(statement))

        for statement in LOGISTICS_INDEXES:
            connection.execute(text(statement))
