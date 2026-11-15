"""Mocked API tests; no live external request or account required."""
from integrations.aviation import airlabs_flight, opensky_near_airport, flight_matches_route

class Response:
    def __init__(self, payload): self.payload=payload
    def raise_for_status(self): pass
    def json(self): return self.payload

class Session:
    def __init__(self, payload): self.payload=payload
    def get(self, *args, **kwargs): return Response(self.payload)

def test_airlabs_not_configured(monkeypatch):
    monkeypatch.delenv("AIRLABS_API_KEY", raising=False)
    assert airlabs_flight("6E203", session=Session({}))["status"]=="not_configured"

def test_airlabs_exact_flight_number():
    records={"response":[
        {"flight_iata":"6E203","dep_iata":"HYD","arr_iata":"DEL"},
        {"flight_iata":"AI203","dep_iata":"HYD","arr_iata":"DEL"}]}
    result=airlabs_flight("6E203",api_key="fake",session=Session(records))
    assert len(result["flights"])==1
    assert len(flight_matches_route(result["flights"],"HYD","DEL"))==1

def test_airlabs_quota_errors():
    assert airlabs_flight("6E203",api_key="fake",
                          session=Session({"error":{"message":"quota"}}))["status"]=="error"

def test_opensky_nearby_not_schedule():
    states={"time":123456,"states":[
        ["abc123","IGO203",None,None,None,78.4,17.2,None,False,180,95]]}
    result=opensky_near_airport(17.24,78.43,session=Session(states))
    assert result["status"]=="ok"
    assert result["aircraft"][0]["callsign"]=="IGO203"
    assert "departure_delay" not in result["aircraft"][0]

def test_opensky_empty():
    assert opensky_near_airport(17,78,session=Session({"time":1,"states":None}))["aircraft"]==[]
