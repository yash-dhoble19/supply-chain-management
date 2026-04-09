
import sys
try:
    from prophet import Prophet
    print("Prophet is installed and importable.")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
