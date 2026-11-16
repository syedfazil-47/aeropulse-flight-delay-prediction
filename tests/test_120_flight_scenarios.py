"""100+ deterministic flight scenarios test matching and route integrity.

These are synthetic API fixtures for automated regression tests, NOT
100 real scheduled flights or actual historical delay observations.
"""
from datetime import date, timedelta, datetime
import pytest
from integrations.flight_profile import choose_flight, known_carrier, normalize_flight
from ml.features import AIRPORTS, AIRLINES, build_features

BASE = date(2026, 11, 16)
CODES = list(AIRPORTS)
PREFIXES = list(AIRLINES)

@pytest.mark.parametrize("case", range(120))
def test_120_flight_profiles_and_model_features(case):
    prefix = PREFIXES[case % len(PREFIXES)]
    flight = f"{prefix}{100 + case}"
    origin = CODES[case % len(CODES)]
    destination = CODES[(case + 9) % len(CODES)]
    travel_date = BASE + timedelta(days=case % 7)
    departure = datetime.combine(travel_date, datetime.min.time()).replace(hour=6 + case % 14)
    data = {
        "flight_iata":flight,
        "dep_iata":origin,
        "arr_iata":destination,
        "dep_time": departure.isoformat(timespec="minutes"),
        "arr_time":departure.isoformat(timespec="minutes"),
        "status":"scheduled",
    }
    selected = choose_flight([data], f" {flight} ", travel_date)
    assert selected is data
    assert selected["dep_iata"] == origin and selected["arr_iata"] == destination
    assert known_carrier(flight, AIRLINES) == AIRLINES[prefix]
    features=build_features(flight,origin,destination,departure)
    assert features["origin_code"] == origin
    assert features["destination_code"] == destination
    assert features["departure_hour"] == departure.hour
    # A single changed date MUST reject otherwise matching flight records.
    assert choose_flight([data],flight,travel_date+timedelta(days=1)) is None
    # A differently numbered flight MUST NOT masquerade as this one.
    assert choose_flight([data],prefix+"99999",travel_date) is None

def test_missing_date_cannot_be_confirmed():
    row={"flight_iata":"6E203","dep_iata":"HYD","arr_iata":"DEL","dep_time":None}
    assert choose_flight([row],"6E203",BASE) is None

def test_missing_route_cannot_be_confirmed():
    row={"flight_iata":"6E203","dep_iata":"HYD","arr_iata":None,
         "dep_time":"2026-11-16T18:00"}
    assert choose_flight([row],"6E203",BASE) is None

def test_normalization():
    assert normalize_flight(" 6e 203  ")=="6E203"
