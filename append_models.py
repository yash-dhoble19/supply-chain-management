with open('models.py', 'a') as f:
    f.write('''
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
''')

# anything
