"""External aviation sources. Live observations are not flight-delay predictions."""
import os
import re
import requests

AIRLABS_URL = "https://airlabs.co/api/v9/flights"
OPENSKY_URL = "https://opensky-network.org/api/states/all"
OPENSKY_TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

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

def opensky_access_token(client_id, client_secret, session=None):
    """Exchange OpenSky OAuth2 client credentials for a short-lived access token.

    Report safe, actionable error categories without leaking credentials,
    request bodies, or potentially sensitive server responses.
    """
    if not client_id or not client_secret:
        return {"status": "not_configured", "message": "OpenSky client credentials are incomplete"}
    http = session or requests
    try:
        response = http.post(OPENSKY_TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": client_id.strip(), "client_secret": client_secret.strip(),
        }, headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=(5, 15))
        code = getattr(response, "status_code", 200)
        if code in (400, 401, 403):
            return {"status": "auth_error", "message": f"OpenSky authentication rejected (HTTP {code}); check the API client ID and secret"}
        if code == 429:
            return {"status": "rate_limited", "message": "OpenSky token endpoint is rate limiting requests (HTTP 429)"}
        if code >= 500:
            return {"status": "server_error", "message": f"OpenSky authentication server returned HTTP {code}"}
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            return {"status": "invalid_response", "message": "OpenSky token response did not contain an access token"}
        return {"status": "ok", "token": token}
    except requests.Timeout:
        return {"status": "timeout", "message": "OpenSky authentication server timed out from Streamlit hosting"}
    except requests.ConnectionError:
        return {"status": "connection_error", "message": "Streamlit hosting could not connect to OpenSky authentication server (network, DNS, or IP restriction)"}
    except requests.HTTPError:
        return {"status": "http_error", "message": "OpenSky token endpoint returned an unexpected HTTP error"}
    except (requests.RequestException, ValueError):
        return {"status": "invalid_response", "message": "OpenSky authentication response could not be processed"}


def opensky_near_airport(latitude, longitude, radius_deg=0.35, token=None, session=None):
    """Nearby aircraft states, NOT a flight schedule or a flight-delay observation."""
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
        code = getattr(response, "status_code", 200)
        if code == 429:
            return {"status": "rate_limited", "message": "OpenSky request limit reached", "aircraft": []}
        if code == 401:
            return {"status": "auth_error", "message": "OpenSky rejected authentication", "aircraft": []}
        if code == 403:
            return {"status": "forbidden", "message": "OpenSky access denied for this connection", "aircraft": []}
        if code >= 500:
            return {"status": "unavailable", "message": "OpenSky server temporarily unavailable", "aircraft": []}
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
    except requests.Timeout:
        return {"status": "unavailable", "message": "OpenSky request timed out", "aircraft": []}
    except (requests.RequestException, ValueError):
        return {"status": "unavailable", "message": "OpenSky connection or response error", "aircraft": []}



ADSB_LOL_API = "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{km}"

def adsb_lol_near_airport(latitude, longitude, radius_km=80, session=None):
    """Independent community aircraft feed, explicitly sourced from adsb.lol.

    Returns nearby aircraft observations, NOT schedule status or delay labels.
    Public API licensed under ODbL 1.0; show attribution in the UI.
    """
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Invalid coordinates")
    radius_km = max(10, min(int(radius_km), 100))
    url = ADSB_LOL_API.format(
        lat=f"{latitude:.4f}", lon=f"{longitude:.4f}", km=radius_km
    )
    http = session or requests
    try:
        response = http.get(
            url,
            headers={"User-Agent": "AeroPulse-FlightIntelligence/1.0 (+https://github.com/syedfazil-47/aeropulse-flight-delay-prediction)",
                     "Accept": "application/json"},
            timeout=(3, 6),
        )
        code = getattr(response, "status_code", 200)
        if code == 429:
            return {"status": "rate_limited", "aircraft": [], "source": "adsb.lol"}
        if code in (401, 403):
            return {"status": "access_denied", "aircraft": [], "source": "adsb.lol"}
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("ac"), list):
            return {"status": "invalid_response", "aircraft": [], "source": "adsb.lol"}
        aircraft = []
        for record in payload["ac"][:250]:
            if not isinstance(record, dict):
                continue
            lat, lon = record.get("lat"), record.get("lon")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                continue
            age = record.get("seen_pos")
            if isinstance(age, (int, float)) and age > 90:
                continue
            aircraft.append({
                "callsign": str(record.get("flight") or "").strip(),
                "icao24": record.get("hex"), "latitude": lat, "longitude": lon,
                "on_ground": record.get("alt_baro") == "ground",
                "velocity_kts": record.get("gs"), "heading": record.get("track"),
            })
        return {"status": "ok", "aircraft": aircraft, "source": "adsb.lol",
                "timestamp": payload.get("now")}
    except requests.Timeout:
        return {"status": "timeout", "aircraft": [], "source": "adsb.lol"}
    except (requests.RequestException, ValueError):
        return {"status": "unavailable", "aircraft": [], "source": "adsb.lol"}

def flight_matches_route(records, origin, destination):
    """Require explicit matching departure and arrival codes."""
    return [r for r in records if r.get("dep_iata") == origin and r.get("arr_iata") == destination]
