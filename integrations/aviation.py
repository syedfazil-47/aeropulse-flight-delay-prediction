"""External aviation sources. Live observations are not flight-delay predictions."""
import os
import re
import requests

AIRLABS_URL = "https://airlabs.co/api/v9/flights"
OPENSKY_URL = "https://opensky-network.org/api/states/all"

def airlabs_flight(flight_number, api_key=None, session=None):
    """Query live flight records, matching flight numbers exactly."""
    key = api_key or os.getenv("AIRLABS_API_KEY")
    if not key:
        return {"status": "not_configured", "message": "AirLabs API key not configured", "flights": []}
    flight = re.sub(r"\s+", "", flight_number.upper())
    if not re.fullmatch(r"[A-Z0-9]{3,8}", flight):
        raise ValueError("Invalid flight number")
    http = session or requests
    try:
        response = http.get(AIRLABS_URL, params={"api_key": key, "flight_iata": flight}, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected AirLabs response")
        if payload.get("error"):
            return {"status": "error", "message": "AirLabs API error (check plan, quota or key)", "flights": []}
        records = payload.get("response", [])
        if not isinstance(records, list):
            raise ValueError("Unexpected AirLabs flight list")
        matching = [r for r in records if isinstance(r, dict) and
                    str(r.get("flight_iata", "")).replace(" ", "").upper() == flight]
        allowed = ("flight_iata", "airline_iata", "dep_iata", "arr_iata",
                   "status", "dep_time", "arr_time", "dep_estimated",
                   "arr_estimated", "dep_actual", "arr_actual", "updated")
        return {"status": "ok" if matching else "not_found",
                "message": "Live records found" if matching else "No matching current flight",
                "flights": [{k: r.get(k) for k in allowed if r.get(k) is not None}
                            for r in matching[:10]]}
    except (requests.RequestException, ValueError):
        return {"status": "unavailable", "message": "AirLabs unavailable or response invalid", "flights": []}

def opensky_near_airport(latitude, longitude, radius_deg=0.35, token=None, session=None):
    """Nearby aircraft states, not a flight schedule or reliable specific-flight match."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Invalid coordinates")
    radius_deg = max(0.05, min(float(radius_deg), 0.8))
    http = session or requests
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = http.get(OPENSKY_URL, params={
            "lamin": max(-90, latitude-radius_deg), "lamax": min(90, latitude+radius_deg),
            "lomin": max(-180, longitude-radius_deg), "lomax": min(180, longitude+radius_deg),
        }, headers=headers, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("states"), (list, type(None))):
            raise ValueError("Unexpected OpenSky response")
        aircraft = []
        for state in (payload.get("states") or [])[:250]:
            if not isinstance(state, list) or len(state) < 11:
                continue
            aircraft.append({"callsign": str(state[1] or "").strip(),
                             "icao24": state[0], "longitude": state[5], "latitude": state[6],
                             "on_ground": state[8], "velocity_mps": state[9],
                             "heading": state[10]})
        return {"status": "ok", "timestamp": payload.get("time"), "aircraft": aircraft}
    except (requests.RequestException, ValueError):
        return {"status": "unavailable", "message": "OpenSky unavailable", "aircraft": []}

def flight_matches_route(records, origin, destination):
    """Require explicit matching departure and arrival codes."""
    return [r for r in records if r.get("dep_iata") == origin and r.get("arr_iata") == destination]
