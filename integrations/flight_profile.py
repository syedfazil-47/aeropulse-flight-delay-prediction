"""Flight profile selection. Never turn user-entered information into a verified schedule."""
from datetime import date, datetime
import re

def normalize_flight(value):
    return re.sub(r"\s+", "", (value or "").upper())

def _date_of(value):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None

def choose_flight(flights, flight_number, travel_date):
    """Match flight, travel date and both airport codes, otherwise no verified profile.

    Live endpoints may omit timestamps or return a flight on another day.
    Missing date prevents presenting a timetable as verified for user's date.
    """
    flight_number = normalize_flight(flight_number)
    for item in flights or []:
        if normalize_flight(item.get("flight_iata")) != flight_number:
            continue
        if _date_of(item.get("dep_time")) != travel_date:
            continue
        if not (item.get("dep_iata") and item.get("arr_iata")):
            continue
        return item
    return None

def show_time(value):
    if not value or not isinstance(value, str):
        return "Not available"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Display as supplied by provider, without assuming airport-local timezone.
        return dt.strftime("%d %b · %H:%M") + (" (API timezone)" if dt.tzinfo is None else " (offset shown in API)")
    except ValueError:
        return str(value)[:32]

def known_carrier(flight_number, carriers):
    number=normalize_flight(flight_number)
    for prefix in sorted(carriers,key=len,reverse=True):
        if number.startswith(prefix) and number[len(prefix):].isdigit():
            return carriers[prefix]
    return "Carrier not confirmed"
