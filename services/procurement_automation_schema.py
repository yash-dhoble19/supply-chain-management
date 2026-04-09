"""
Schema migration for procurement automation tables.
Aligns the database with BOTH the existing FastAPI models AND
the n8n workflow's PostgreSQL node expectations.

n8n writes directly to `email_interactions` and `suppliers` using
specific column names — this migration ensures compatibility.
"""
from sqlalchemy import text


# ─── Supplier table: columns n8n needs ───────────────────────────
SUPPLIER_N8N_COLUMNS = [
    # n8n queries `WHERE supplier_id = X` but our PK is `id`.
    # Create a generated column so both work.
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'suppliers' AND column_name = 'supplier_id'
        ) THEN
            ALTER TABLE suppliers ADD COLUMN supplier_id INTEGER;
            UPDATE suppliers SET supplier_id = id WHERE supplier_id IS NULL;
            CREATE INDEX IF NOT EXISTS ix_suppliers_supplier_id ON suppliers (supplier_id);
        END IF;
    END $$;
    """,
    # n8n reads `contact_name` but our model has `contact_person`
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_name VARCHAR",
    # n8n writes these columns on reply/escalation
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS last_reply_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS latest_quote_price DOUBLE PRECISION",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS latest_quote_delivery VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS responsiveness_status VARCHAR DEFAULT 'normal'",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS last_escalation_at TIMESTAMP WITH TIME ZONE",
    # Our procurement automation fields
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'INTERNAL'",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS source_url VARCHAR",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS source_scraped_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS responsiveness_flag VARCHAR DEFAULT 'NORMAL'",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS last_response_time_hours DOUBLE PRECISION",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS total_inquiries_sent INTEGER DEFAULT 0",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS total_replies_received INTEGER DEFAULT 0",
]


SUPPLIER_N8N_BACKFILL = [
    # Sync supplier_id = id for all existing rows
    "UPDATE suppliers SET supplier_id = id WHERE supplier_id IS NULL OR supplier_id != id",
    # Sync contact_name from contact_person
    "UPDATE suppliers SET contact_name = COALESCE(contact_name, contact_person) WHERE contact_name IS NULL",
    # Defaults
    "UPDATE suppliers SET source = COALESCE(source, 'INTERNAL') WHERE source IS NULL",
    "UPDATE suppliers SET responsiveness_flag = COALESCE(responsiveness_flag, 'NORMAL') WHERE responsiveness_flag IS NULL",
    "UPDATE suppliers SET responsiveness_status = COALESCE(responsiveness_status, 'normal') WHERE responsiveness_status IS NULL",
    "UPDATE suppliers SET total_inquiries_sent = COALESCE(total_inquiries_sent, 0) WHERE total_inquiries_sent IS NULL",
    "UPDATE suppliers SET total_replies_received = COALESCE(total_replies_received, 0) WHERE total_replies_received IS NULL",
]


# ─── email_interactions table: match n8n's column names ──────────
# n8n writes to these exact column names. Our model must use the same.
# The table is created by SQLAlchemy create_all, but any renames from
# the previous version need to be handled here.
EMAIL_INTERACTIONS_COMPAT = [
    # If old column names exist from previous model, rename them
    """
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'email_interactions' AND column_name = 'gmail_message_id'
        ) THEN
            ALTER TABLE email_interactions RENAME COLUMN gmail_message_id TO message_id;
        END IF;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'email_interactions' AND column_name = 'gmail_thread_id'
        ) THEN
            ALTER TABLE email_interactions RENAME COLUMN gmail_thread_id TO thread_id;
        END IF;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'email_interactions' AND column_name = 'email_subject'
        ) THEN
            ALTER TABLE email_interactions RENAME COLUMN email_subject TO subject;
        END IF;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'email_interactions' AND column_name = 'email_body_preview'
        ) THEN
            ALTER TABLE email_interactions RENAME COLUMN email_body_preview TO body;
        END IF;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'email_interactions' AND column_name = 'last_followup_at'
        ) THEN
            ALTER TABLE email_interactions RENAME COLUMN last_followup_at TO follow_up_sent_at;
        END IF;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'email_interactions' AND column_name = 'replied_at'
        ) THEN
            ALTER TABLE email_interactions RENAME COLUMN replied_at TO received_at;
        END IF;
    END $$;
    """,
    # Add columns n8n needs that may not exist yet
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS message_id VARCHAR",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS thread_id VARCHAR",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS subject TEXT",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS body TEXT",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS email_type VARCHAR",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS recipient_email VARCHAR",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS sender_email VARCHAR",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS inquiry_details TEXT",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS extracted_data TEXT",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE email_interactions ADD COLUMN IF NOT EXISTS follow_up_sent_at TIMESTAMP WITH TIME ZONE",
    # Make session_id nullable since n8n doesn't write sessions
    """
    DO $$ BEGIN
        ALTER TABLE email_interactions ALTER COLUMN session_id DROP NOT NULL;
    EXCEPTION WHEN others THEN NULL;
    END $$;
    """,
]


# ─── Indexes ─────────────────────────────────────────────────────
AUTOMATION_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_suppliers_source ON suppliers (source)",
    "CREATE INDEX IF NOT EXISTS ix_suppliers_supplier_id ON suppliers (supplier_id)",
    "CREATE INDEX IF NOT EXISTS ix_ei_session ON email_interactions (session_id)",
    "CREATE INDEX IF NOT EXISTS ix_ei_supplier ON email_interactions (supplier_id)",
    "CREATE INDEX IF NOT EXISTS ix_ei_status ON email_interactions (status)",
    "CREATE INDEX IF NOT EXISTS ix_ei_thread ON email_interactions (thread_id)",
    "CREATE INDEX IF NOT EXISTS ix_sq_session ON supplier_quotes (session_id)",
    "CREATE INDEX IF NOT EXISTS ix_sq_supplier ON supplier_quotes (supplier_id)",
    "CREATE INDEX IF NOT EXISTS ix_eil_interaction ON email_interaction_logs (interaction_id)",
]


# ─── Trigger: auto-sync supplier_id = id on INSERT ──────────────
SUPPLIER_ID_SYNC_TRIGGER = """
DO $$ BEGIN
    CREATE OR REPLACE FUNCTION sync_supplier_id()
    RETURNS TRIGGER AS $func$
    BEGIN
        NEW.supplier_id := NEW.id;
        RETURN NEW;
    END;
    $func$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_sync_supplier_id ON suppliers;
    CREATE TRIGGER trg_sync_supplier_id
        BEFORE INSERT OR UPDATE ON suppliers
        FOR EACH ROW
        EXECUTE FUNCTION sync_supplier_id();
EXCEPTION WHEN others THEN NULL;
END $$;
"""


def sync_procurement_automation_schema(engine) -> None:
    """Run idempotent schema migration for procurement automation."""
    with engine.begin() as connection:
        # Supplier columns for n8n compatibility
        for statement in SUPPLIER_N8N_COLUMNS:
            try:
                connection.execute(text(statement))
            except Exception as e:
                print(f"[schema migration warning] {e}")

        # Backfill supplier data
        for statement in SUPPLIER_N8N_BACKFILL:
            try:
                connection.execute(text(statement))
            except Exception as e:
                print(f"[schema backfill warning] {e}")

        # email_interactions compatibility
        for statement in EMAIL_INTERACTIONS_COMPAT:
            try:
                connection.execute(text(statement))
            except Exception as e:
                print(f"[schema compat warning] {e}")

        # Indexes
        for statement in AUTOMATION_INDEXES:
            try:
                connection.execute(text(statement))
            except Exception as e:
                pass  # Index may already exist

        # Supplier ID sync trigger
        try:
            connection.execute(text(SUPPLIER_ID_SYNC_TRIGGER))
        except Exception as e:
            print(f"[trigger warning] {e}")

# anything
