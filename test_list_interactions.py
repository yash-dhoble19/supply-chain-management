import json
import traceback
from database import SessionLocal
from services.procurement_automation_service import list_interactions

db = SessionLocal()
try:
    print("Testing list interactions...")
    res = list_interactions(db)
    print("Success! Items:", len(res["items"]))
except Exception as e:
    traceback.print_exc()

# anything
