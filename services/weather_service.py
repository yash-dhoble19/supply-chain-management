import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("Weather_API_KEY") or os.getenv("VITE_WEATHER_API_KEY")

def get_weather_forecast(location: str) -> str:
    """
    Fetches the current weather for a specific location.
    If the API fails or is not provided, returns a stable fallback.
    """
    if not location or location.strip() == "":
        location = "India"
        
    if not WEATHER_API_KEY:
        return f"Weather API Key not configured. Fallback: Expecting typical seasonal patterns for {location}."
        
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            condition = data["weather"][0]["description"].title()
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            return f"{condition}, {temp}°C with {humidity}% humidity in {location}."
        else:
            # Fallback when location not found or API limits exceeded
            return f"Fallback: Historical seasonal weather metrics applied for {location}."
    except Exception as e:
        # Fallback for network issues, timeouts, etc.
        return f"Fallback: Stable weather assumed for {location} due to API unavailability."
