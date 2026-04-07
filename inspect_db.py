from database import SessionLocal
import models
import json

def inspect_shipment(tracking_number):
    db = SessionLocal()
    try:
        s = db.query(models.Shipment).filter(models.Shipment.tracking_number == tracking_number).first()
        if not s:
            print(f"❌ Shipment {tracking_number} not found.")
            return
            
        print(f"📦 Shipment Info: {s.tracking_number}")
        print(f"   Status: {s.status}")
        print(f"   Origin Address: {s.origin}")
        print(f"   Origin Coords (Stored): {s.origin_lat}, {s.origin_lon}")
        print(f"   Current Coords: {s.current_location_lat}, {s.current_location_lon}")
        print(f"   Progress: {s.progress_percent}%")
        print(f"   Total Distance: {s.total_distance_km} km")
        print(f"   Created At: {s.created_at}")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Use the tracking number from the screenshot
    inspect_shipment("TRK-1769541002")
    # Also list all shipments to see if there are others
    print("\n📋 All Recent Shipments:")
    db = SessionLocal()
    for s in db.query(models.Shipment).order_by(models.Shipment.id.desc()).limit(5).all():
        print(f"   - {s.tracking_number} | Status: {s.status} | Progress: {s.progress_percent}%")
    db.close()
