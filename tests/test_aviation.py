"""Mocked API tests; no live external request or account required."""
from integrations.aviation import airlabs_flight, opensky_near_airport, opensky_access_token, flight_matches_route

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

class HttpResponse:
    def __init__(self, status_code, payload=None):
        self.status_code=status_code
        self.payload=payload or {}
    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))
    def json(self): return self.payload

class HttpSession:
    def __init__(self, response): self.response=response
    def get(self, *args, **kwargs): return self.response
    def post(self, *args, **kwargs): return self.response

def test_opensky_rate_limit_message():
    result=opensky_near_airport(17.24,78.43,session=HttpSession(HttpResponse(429)))
    assert result["status"]=="rate_limited"

def test_opensky_auth_denied():
    result=opensky_near_airport(17.24,78.43,token="expired",session=HttpSession(HttpResponse(401)))
    assert result["status"]=="auth_error"

def test_opensky_oauth_token_issued():
    result=opensky_access_token("client","secret",session=HttpSession(HttpResponse(200,{"access_token":"sample-token"})))
    assert result["status"]=="ok"
    assert result["token"]=="sample-token"

def test_opensky_oauth_bad_credentials():
    result=opensky_access_token("bad","bad",session=HttpSession(HttpResponse(401)))
    assert result["status"]=="auth_error"

def test_opensky_forbidden():
    result=opensky_near_airport(17.24,78.43,session=HttpSession(HttpResponse(403)))
    assert result["status"]=="forbidden"
