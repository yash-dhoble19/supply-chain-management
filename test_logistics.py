import requests
import time
from geopy.geocoders import Nominatim

API_URL = "http://127.0.0.1:8000"

def test_logistics_flow():
    print("🚀 Starting End-to-End Logistics Test: Amravati -> Daryapur")
    
    # 1. Create Carrier & Driver
    print("\n1. Setting up Carrier & Driver...")
    c_name = f"Test Carrier {int(time.time())}"
    c_res = requests.post(f"{API_URL}/logistics/carriers/create", json={
        "name": c_name, "contact_info": "123", "fleet_size": 10
    })
    
    if c_res.status_code != 200:
        print(f"❌ Error creating carrier: {c_res.text}")
        return
    carrier_id = c_res.json()['id']
    
    d_res = requests.post(f"{API_URL}/logistics/drivers/create", json={
        "name": "Test Driver", "license_number": f"MH-{int(time.time())}", "carrier_id": carrier_id
    })
    
    if d_res.status_code != 200:
        print(f"❌ Error creating driver: {d_res.text}")
        return
    driver_id = d_res.json()['id']
    print(f"   ✅ Carrier ID: {carrier_id}, Driver ID: {driver_id}")

    # 2. Schedule Shipment
    print("\n2. Scheduling Shipment (Amravati -> Daryapur)...")
    tracking_num = f"TRK-{int(time.time())}"
    shipment_payload = {
        "tracking_number": tracking_num,
        "origin": "Amravati, Maharashtra, India",
        "destination": "Daryapur, Maharashtra, India",
        "carrier_id": carrier_id,
        "driver_id": driver_id,
        "waypoints": [],
        "scheduled_date": "2024-02-01T10:00:00"
    }
    s_res = requests.post(f"{API_URL}/logistics/shipments/create", json=shipment_payload)
    if s_res.status_code != 200:
        print(f"❌ Error creating shipment: {s_res.text}")
        return
        
    shipment = s_res.json()
    shipment_id = shipment['id']
    print(f"   ✅ Shipment Created! ID: {shipment_id}")
    print(f"   📍 Origin Coords Stored: {shipment.get('origin_lat')}, {shipment.get('origin_lon')}")
    
    # 3. Simulate Tracking Updates
    print("\n3. Testing Tracking & Progress Calculation...")
    
    # Coordinates (Approximate)
    amravati_coords = (20.9320, 77.7523) # Start
    midway_coords = (20.9450, 77.5500)   # Somewhere between
    daryapur_coords = (20.9570, 77.3480) # End
    
    # Test A: At Origin (Should be 0%)
    print("\n   [Test A] Driver at Origin (Amravati)...")
    requests.post(f"{API_URL}/logistics/shipments/{shipment_id}/update", json={
        "current_location_lat": amravati_coords[0],
        "current_location_lon": amravati_coords[1],
        "status": "IN_TRANSIT"
    })
    
    s_check = requests.get(f"{API_URL}/logistics/shipments/list").json()
    s_data = next(s for s in s_check if s['id'] == shipment_id)
    print(f"   📊 Progress: {s_data['progress_percent']}% (Expected: ~0%)")
    
    if s_data['progress_percent'] < 1.0:
        print("   ✅ PASS: Progress is effectively 0% at origin.")
    else:
        print("   ❌ FAIL: Progress is significantly > 0% at origin.")

    # Test B: Midway
    print("\n   [Test B] Driver Midway...")
    requests.post(f"{API_URL}/logistics/shipments/{shipment_id}/update", json={
        "current_location_lat": midway_coords[0],
        "current_location_lon": midway_coords[1]
    })
    s_check = requests.get(f"{API_URL}/logistics/shipments/list").json()
    s_data = next(s for s in s_check if s['id'] == shipment_id)
    print(f"   📊 Progress: {s_data['progress_percent']}% (Expected: ~30-60%)")

    print("\n✅ Test Complete.")

if __name__ == "__main__":
    test_logistics_flow()
