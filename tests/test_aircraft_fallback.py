"""Contract tests for adsb.lol fallback; never contact production APIs."""
from integrations.aviation import adsb_lol_near_airport
import requests

class Reply:
    status_code = 200
    def __init__(self, value): self.value = value
    def raise_for_status(self): pass
    def json(self): return self.value

class Session:
    def __init__(self, response): self.response = response; self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

def test_aircraft_data_parses_and_discards_stale_positions():
    session = Session(Reply({"now":1234, "ac":[
        {"flight":"IGO123 ", "hex":"abc123", "lat":17.3,"lon":78.4,"seen_pos":3,"gs":212},
        {"hex":"def456", "lat":17.4,"lon":78.5,"seen_pos":120},
        {"hex":"xyz789","seen_pos":2}
    ]}))
    result=adsb_lol_near_airport(17.2403,78.4294,session=session)
    assert result["status"]=="ok"
    assert result["source"]=="adsb.lol"
    assert len(result["aircraft"])==1
    assert result["aircraft"][0]["callsign"]=="IGO123"
    assert "/lat/17.2403/lon/78.4294/dist/80" in session.calls[0][0]
    assert session.calls[0][1]["timeout"] == (3, 6)

def test_empty_area_is_success_not_failure():
    assert adsb_lol_near_airport(17,78,session=Session(Reply({"ac":[]})))["status"]=="ok"

def test_invalid_payload_does_not_claim_zero_aircraft():
    assert adsb_lol_near_airport(17,78,session=Session(Reply({})))["status"]=="invalid_response"

def test_timeout_is_safe_and_bounded():
    class TimedOut:
        def get(self, *args, **kwargs): raise requests.Timeout("private details")
    result=adsb_lol_near_airport(17,78,session=TimedOut())
    assert result["status"]=="timeout"
    assert "private" not in str(result)

def test_limits_radius():
    session=Session(Reply({"ac":[]}))
    adsb_lol_near_airport(17,78,radius_km=99999,session=session)
    assert session.calls[0][0].endswith("/dist/100")
