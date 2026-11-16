# AeroPulse · India Flight Intelligence

Bright, mobile-friendly aviation dashboard built with Streamlit, Plotly, and scikit-learn.

## New dashboard
- Light white-and-sky-blue airline-style interface with route and carrier summary.
- Manual input: flight number, travel date, departure time, departure and destination airports.
- **Strict live flight verification**: a flight number, travel date, and reported origin/destination must match an AirLabs response before the app labels the profile verified. Otherwise displayed route and time are **user-entered**, not official airline schedule information.
- Two circular delay-risk charts (departure and arrival) for an **experimental synthetic-data classifier**. The figures are illustrative, not real forecast accuracy.
- Airport weather forecast via Open-Meteo (when available).
- Nearby aircraft: separate, optional ADS-B count by adsb.lol (ODbL 1.0). This does not establish that the searched flight is tracked.
- OpenSky OAuth2 integration remains in the repository for diagnostic use; the cloud endpoint previously timed out.

## Deploy
Streamlit Community Cloud: main module `app/main.py`.
```bash
pip install -r requirements.txt
streamlit run app/main.py
```

Set `AIRLABS_API_KEY = "..." ` in Streamlit's private Secrets settings. **Never commit API credentials.** API coverage and monthly quotas depend on your plan. An API that provides current flight observations does not necessarily provide future timetable records.

## Validation
```bash
python -m pytest -q
```
The suite includes **120 parametrized flight-profile fixtures** across airport/airline/date combinations, plus input validation, provider failure handling, historical model-training workflow tests, and a Streamlit startup smoke test. **These simulated fixtures are not 120 real upcoming flights.** Testing actual flight coverage requires independently sourced real flight IDs and available provider records.

## Training a real model
`ml/real_training.py` is a strictly separated trainer for **genuine observed history**, never hypothetical future outcomes. It accepts a CSV with:
```text
flight_date,airline_code,origin_code,destination_code,scheduled_departure_hour,departure_delay_minutes,arrival_delay_minutes
```

Requirements:
- Each row must be a completed flight with legally usable observed delays (scheduled vs actual times).
- At least 200 valid rows across 10 or more distinct flight dates for the minimum pipeline sanity check; **significantly more diverse history is necessary for credible accuracy**.
- Trains on earlier dates, evaluates on later dates, and reports ROC-AUC and Brier score for departure/arrival.
- Uses schedule-time features only; no label leakage from actual results to predictors.

Run explicitly when a compliant historical dataset has been independently verified:
```bash
python -m ml.real_training --history path/to/observed_flights.csv --output ml
```

This release **does not contain historical labels or validated real-world models**, so the dashboard continues to label its risk charts as experimental. We will not invent a model's accuracy.

## Coverage limitations
- This is not an official airline or government service.
- Flight lookup availability varies by AirLabs subscription and region; future date coverage may be absent.
- The airport directory includes a selected set of Indian cities; unsupported routes still display a provider-reported flight profile but may not have weather or experimental risk calculations.
- Manual inputs are never represented as verified schedules.
- Weather at arrival airport is sampled at the selected departure hour; not a calculated touchdown-time forecast.
- Community aircraft counts are unrelated to the specific searched flight unless identity correlation is verified.
- For current flights and travel decisions, confirm with the airline or airport.
