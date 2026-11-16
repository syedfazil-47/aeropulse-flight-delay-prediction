# AeroPulse — Midnight Aviation (Phase 2)

An Indian domestic aviation dashboard with **three live data-source integrations**:
- **AirLabs** — lookup for current flight records by flight number, when your API plan and coverage permit.
- **OpenSky Network** — anonymous nearby-aircraft location observations near the departure/arrival airports.
- **Open-Meteo** — weather forecasts at departure and arrival airports for the user-selected departure time.

> **Predictions remain SYNTHETIC demonstration model scores.** These live observations do **not** inform the model, provide a reliable future flight schedule, or establish measured predictive accuracy. Never use the demo estimates for travel decisions.

## Deploy and connect
1. Main file: `app/main.py`; Python dependencies in `requirements.txt`.
2. In **Streamlit Community Cloud → App settings → Secrets**, set:
   ```toml
   AIRLABS_API_KEY = "your-private-airlabs-key"
   ```
3. Never commit a real API key or `.streamlit/secrets.toml`.
4. Open the deployed dashboard, select a flight, and click **Analyze flight**.

**Data behavior:** API calls occur when visitors analyze a flight. Streamlit caches AirLabs for 10 minutes, OpenSky for 5 minutes, and Open-Meteo for 30 minutes (per app instance). OpenSky can restrict anonymous access; AirLabs usage is subject to account limits and endpoint permissions. No scheduled background ingestion or database is included in this phase.

## Local tests
```bash
pip install -r requirements.txt
python -m pytest tests -q
python -m ml.train
streamlit run app/main.py
```

## Limitations
- Some airline flight numbers/selected routes may have no current AirLabs result.
- No current record does **not** mean a flight is cancelled.
- OpenSky nearby aircraft are **not** necessarily the searched flight.
- The selected arrival airport's weather is shown at the entered departure time (not a calculated arrival time).
- Live external requests have not been verified against a real AirLabs account in CI; unit tests use mocked responses.
- To train real delay models, collect legally usable historical records with scheduled and actual times, perform time-separated validation and calibration, and document measured quality.

## OpenSky connectivity troubleshooting (November 2026)
OpenSky anonymous state-vector access can be rate-limited by the server's public IP. AeroPulse now shows distinct messages for HTTP 401 (authentication), 403 (access denied), 429 (quota), timeouts and empty areas.

To use authenticated access, create an **OpenSky API Client** on your OpenSky account page (not a normal website password). Add the following keys to **Streamlit App settings → Secrets**:
```toml
OPENSKY_CLIENT_ID = "your-opensky-client-id"
OPENSKY_CLIENT_SECRET = "your-opensky-client-secret"
```
The dashboard automatically requests an OAuth2 access token, caches it for 25 minutes, and uses it for up to 5-minute-cached nearby aircraft lookups. **Never commit these credentials to GitHub.** OpenSky can still reject requests or report zero nearby aircraft. These data cannot verify airline schedules or flight delays.

Official API docs: https://openskynetwork.github.io/opensky-api/rest.html

## November 2026: Resilient aircraft tracking
OpenSky's OAuth token server times out from the current Streamlit hosting environment. OpenSky's maintainers explicitly warn that they may block some cloud and hyperscaler IP ranges. **No programmatic change can guarantee OpenSky will respond from that host**. AeroPulse therefore does not contact OpenSky during a normal flight analysis; this eliminates the recurring 15-second authentication timeout as a dependency.

Nearby-aircraft information now comes from **adsb.lol**, an independent community ADS-B feed (https://www.adsb.lol/docs/open-data/api). Its public API is licensed under **Open Database License 1.0 (ODbL)**. The app attributes the source and restricts usage to a 5-minute local cache, 80 km search radius, and 6-second response timeout. Position availability and uptime depend on provider coverage and access policies, so even this feed cannot guarantee observations.

For diagnostic purposes, advanced users may opt into **"test OpenSky directly"** during a flight search; OpenSky's existing OAuth credentials remain private in Streamlit Secrets and are never sent to the fallback provider. If OpenSky access becomes possible from another hosting IP, it can be re-enabled as a primary source after verification. Neither provider verifies a specific flight's planned route or delay.
