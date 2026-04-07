-- Add PublishedGoods table for global published goods
CREATE TABLE IF NOT EXISTS published_goods (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    unit_price FLOAT NOT NULL,
    image_url TEXT,
    supplier_name VARCHAR,
    published_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);
