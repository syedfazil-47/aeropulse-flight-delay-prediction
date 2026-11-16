"""Prevent regression: adapters must load by local filepath despite namespace collision."""
import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]

def load_file(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "integrations" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_file_based_adapter_loading_ignores_colliding_package(monkeypatch):
    monkeypatch.setitem(sys.modules, "integrations", types.ModuleType("integrations"))
    aviation = load_file("aeropulse_aviation_adapter_test", "aviation.py")
    weather = load_file("aeropulse_weather_adapter_test", "weather.py")
    assert callable(aviation.airlabs_flight)
    assert callable(aviation.opensky_near_airport)
    assert callable(aviation.opensky_access_token)
    assert callable(aviation.flight_matches_route)
    assert callable(weather.fetch_hourly_forecast)
    assert callable(weather.weather_at_hour)
