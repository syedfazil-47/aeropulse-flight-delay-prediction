from datetime import date, datetime
import pytest
from integrations.weather import fetch_hourly_forecast, weather_at_hour

class Response:
    def raise_for_status(self): pass
    def json(self):
        return {"hourly":{"time":["2026-11-17T18:00"],
            "temperature_2m":[28], "precipitation_probability":[10],
            "wind_speed_10m":[15], "visibility":[12000]}}

class Session:
    def get(self,*args,**kwargs): return Response()

def test_weather_hour_lookup():
    hourly=fetch_hourly_forecast(17.24,78.43,date(2026,11,17),session=Session())
    result=weather_at_hour(hourly,datetime(2026,11,17,18,30))
    assert result["Temperature (°C)"]==28
    assert result["Rain chance (%)"]==10

def test_missing_weather_hour():
    with pytest.raises(ValueError):
        weather_at_hour({"time":[]},datetime(2026,11,17,18,30))
