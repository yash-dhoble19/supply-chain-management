import requests
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import EmailInteraction, Supplier

def simulate_reply():
    db = SessionLocal()
    
    # 1. Find the most recently triggered interaction that is waiting for a reply
    interaction = db.query(EmailInteraction).filter(
        EmailInteraction.status.in_(["inquiry_pending", "sent"])
    ).order_by(EmailInteraction.id.desc()).first()

    if not interaction:
        print("❌ Could not find any pending interactions. Did you click 'Launch AI Campaign' in the Dashboard first?")
        return

    supplier = db.query(Supplier).filter(Supplier.id == interaction.supplier_id).first()
    
    print(f"📦 Found pending campaign for: {supplier.name} (Email: {supplier.contact_email})")
    
    # 2. Simulate n8n webhook payload for a reply
    webhook_url = "http://localhost:8000/api/webhooks/supplier-replied"
    
    payload = {
        "supplierId": supplier.id,
        "companyName": supplier.company_name,
        "senderEmail": supplier.contact_email,
        "subject": "Re: Inquiry for Supply",
        "receivedAt": "2026-04-03T14:15:00+05:30",
        "emailBody": f"Yes Yash! We can definitely fulfill your order. We have the stock available right now. Let me know if you would like me to generate a formal quote so we can proceed.",
        "extractedQuote": {
            "has_quote": True,
            "has_pricing": True,
            "quote_details": {
                "unit_price": 45,
                "currency": "USD",
                "delivery_days": 2,
                "status": "Available in Stock"
            }
        }
    }
    
    print(f"🚀 Simulating n8n hitting webhook: {webhook_url}")
    
    try:
        response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print("✅ SUCCESS! The backend processed the simulated reply.")
            print("👁️ Open your React Dashboard -> 'Communication Hub' tab.")
            print("It should now show a green 'Replied' status with a 'View AI Extracted Quote' button!")
        else:
            print(f"❌ Failed to process webhook. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error hitting webhook: {str(e)}")
        
if __name__ == "__main__":
    simulate_reply()
