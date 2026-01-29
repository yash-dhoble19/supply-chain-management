from database import SessionLocal
import models
import json

def test_insertion():
    print("Testing direct DB insertion...")
    db = SessionLocal()
    try:
        s = models.Shipment(
            tracking_number="TEST-INSERT",
            origin="Amravati",
            destination="Daryapur",
            status="SCHEDULED",
            origin_lat=21.0,
            origin_lon=77.0,
            origin_snapped=False,
            current_location_lat=21.0,
            current_location_lon=77.0,
            progress_percent=0.0
        )
        db.add(s)
        db.commit()
        print("✅ Direct insertion successful!")
    except Exception as e:
        print(f"❌ Direct insertion failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_insertion()
