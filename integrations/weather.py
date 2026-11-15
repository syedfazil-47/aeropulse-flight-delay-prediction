"""Open-Meteo hourly forecast adapter for Indian airports."""
from datetime import datetime
import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FIELDS = "temperature_2m,precipitation_probability,wind_speed_10m,visibility"

def fetch_hourly_forecast(latitude, longitude, day, session=None):
    http = session or requests
    response = http.get(FORECAST_URL, params={
        "latitude":latitude,"longitude":longitude,"hourly":FIELDS,
        "timezone":"Asia/Kolkata","start_date":day.isoformat(),"end_date":day.isoformat(),
    }, timeout=12)
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly") if isinstance(payload,dict) else None
    if not isinstance(hourly,dict) or not hourly.get("time"):
        raise ValueError("No forecast available for selected day")
    return hourly

def weather_at_hour(hourly, when):
    target = when.replace(minute=0,second=0,microsecond=0).isoformat(timespec="minutes")
    hours=hourly.get("time",[])
    if target not in hours:
        raise ValueError("Forecast for hour unavailable")
    i=hours.index(target)
    labels={
        "temperature_2m":"Temperature (°C)",
        "precipitation_probability":"Rain chance (%)",
        "wind_speed_10m":"Wind (km/h)",
        "visibility":"Visibility (m)",
    }
    return {label:(hourly.get(key,[None]*len(hours))[i]) for key,label in labels.items()}
