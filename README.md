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
