from sqlalchemy import text


SUPPLIER_COLUMNS = [
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS supplier_code VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS company_name VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_person VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS phone VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS website VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS product_name VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS product_category VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS reliability_percent DOUBLE PRECISION",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS on_time_delivery_percent DOUBLE PRECISION",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS supplier_score DOUBLE PRECISION",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS average_delivery_days INTEGER",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS unit_price DOUBLE PRECISION",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS currency VARCHAR DEFAULT 'USD'",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS minimum_order_quantity INTEGER",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS supplier_type VARCHAR DEFAULT 'Strategic'",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'ACTIVE'",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS preferred_supplier BOOLEAN DEFAULT FALSE",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS address TEXT",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS city VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS state VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS country VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS postal_code VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS gst_number VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS tax_id VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS notes TEXT",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
]


SUPPLIER_BACKFILL = [
    """
    UPDATE suppliers
    SET supplier_code = CONCAT('SUP-', LPAD(id::text, 4, '0'))
    WHERE supplier_code IS NULL OR supplier_code = ''
    """,
    """
    UPDATE suppliers
    SET company_name = COALESCE(company_name, name)
    WHERE company_name IS NULL OR company_name = ''
    """,
    """
    UPDATE suppliers
    SET product_category = COALESCE(product_category, category)
    WHERE product_category IS NULL OR product_category = ''
    """,
    """
    UPDATE suppliers
    SET reliability_percent = COALESCE(reliability_percent, reliability_score, 0)
    WHERE reliability_percent IS NULL
    """,
    """
    UPDATE suppliers
    SET on_time_delivery_percent = GREATEST(0, LEAST(100, COALESCE(on_time_delivery_percent, reliability_percent, reliability_score, 0) - 1.5))
    WHERE on_time_delivery_percent IS NULL
    """,
    """
    UPDATE suppliers
    SET average_delivery_days = COALESCE(average_delivery_days, delivery_speed_days, lead_time_days, 5)
    WHERE average_delivery_days IS NULL
    """,
    """
    UPDATE suppliers
    SET unit_price = COALESCE(unit_price, price_per_unit, 0)
    WHERE unit_price IS NULL
    """,
    """
    UPDATE suppliers
    SET currency = COALESCE(currency, 'USD')
    WHERE currency IS NULL OR currency = ''
    """,
    """
    UPDATE suppliers
    SET supplier_type = COALESCE(supplier_type, 'Strategic')
    WHERE supplier_type IS NULL OR supplier_type = ''
    """,
    """
    UPDATE suppliers
    SET status = COALESCE(status, 'ACTIVE')
    WHERE status IS NULL OR status = ''
    """,
    """
    UPDATE suppliers
    SET preferred_supplier = COALESCE(preferred_supplier, FALSE)
    WHERE preferred_supplier IS NULL
    """,
    """
    UPDATE suppliers
    SET created_at = COALESCE(created_at, NOW()),
        updated_at = COALESCE(updated_at, NOW())
    WHERE created_at IS NULL OR updated_at IS NULL
    """,
]


SUPPLIER_INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_suppliers_supplier_code_unique ON suppliers (supplier_code)",
    "CREATE INDEX IF NOT EXISTS ix_suppliers_status ON suppliers (status)",
    "CREATE INDEX IF NOT EXISTS ix_suppliers_product_category ON suppliers (product_category)",
]


def sync_supplier_schema(engine) -> None:
    with engine.begin() as connection:
        for statement in SUPPLIER_COLUMNS:
            connection.execute(text(statement))

        for statement in SUPPLIER_BACKFILL:
            connection.execute(text(statement))

        for statement in SUPPLIER_INDEXES:
            connection.execute(text(statement))

# anything
