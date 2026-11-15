"""AeroPulse: India domestic flight-delay demo dashboard."""
from datetime import date, datetime, time, timedelta
from pathlib import Path
import os
import sys
import joblib
import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.features import AIRPORTS, AIRLINES, FEATURES, build_features
from integrations.aviation import airlabs_flight, opensky_near_airport, flight_matches_route
from integrations.weather import fetch_hourly_forecast, weather_at_hour

st.set_page_config(page_title='AeroPulse | Flight Intelligence', page_icon='✈️', layout='wide')
st.markdown('''<style>
.stApp {background:linear-gradient(145deg,#070f23 0%,#0c1832 55%,#091226 100%);color:#edf6ff}
[data-testid="stHeader"]{background:transparent}
h1,h2,h3{color:#f0f8ff!important}
[data-testid="stMetric"]{background:#142540;border:1px solid #284b6d;border-radius:14px;padding:18px}
[data-testid="stMetricValue"]{color:#4ee4f5}
.stButton>button[kind="primary"]{background:#00b6d7;color:#061322;border:0;font-weight:800}
.ap-kicker{color:#5ce4f4;font-size:13px;letter-spacing:3px;font-weight:700}
.ap-title{font-size:clamp(36px,5vw,64px);font-weight:850;line-height:1.06;margin:8px 0;color:#f3fbff}
.ap-sub{color:#a8bdd3;font-size:17px;max-width:760px}
.ap-panel{background:#13233e;border:1px solid #2a496b;border-radius:16px;padding:20px;margin:10px 0}
.ap-warn{color:#ffc875}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="ap-kicker">AEROPULSE / AVIATION INTELLIGENCE</div>', unsafe_allow_html=True)
st.markdown('<div class="ap-title">Predict the journey.<br>Prepare for the unexpected.</div>', unsafe_allow_html=True)
st.markdown('<p class="ap-sub">A midnight-inspired AI flight intelligence dashboard for Indian domestic routes.</p>', unsafe_allow_html=True)
st.warning('DEMO MODE — delay scores are synthetic and NOT real-world forecasts. AirLabs, OpenSky, and Open-Meteo provide separate live observations where available. They do not inform the demo ML scores. Do not use for travel decisions.')

left, mid, right = st.columns(3)
left.metric('Coverage', '8 airports', 'Demo routes')
mid.metric('Airlines', '4', 'Demo selection')
right.metric('Prediction horizon', '1–7 days', 'User-entered schedule')

st.subheader('Flight intelligence search')
with st.form('flight_search'):
    a, b, c = st.columns(3)
    flight = a.text_input('Flight number', '6E203', help='Examples: 6E203, AI501, QP1102, IX123')
    origin = b.selectbox('Departure airport', list(AIRPORTS), index=2, format_func=lambda k: f'{k} · {AIRPORTS[k][2]}')
    destination = c.selectbox('Arrival airport', list(AIRPORTS), index=0, format_func=lambda k: f'{k} · {AIRPORTS[k][2]}')
    d, t = st.columns(2)
    travel_date = d.date_input('Travel date', value=date.today() + timedelta(days=1), min_value=date.today(), max_value=date.today() + timedelta(days=7))
    travel_time = t.time_input('Scheduled departure (local airport time)', value=time(18, 30))
    submitted = st.form_submit_button('Analyze flight', type='primary', use_container_width=True)


@st.cache_data(ttl=600, show_spinner=False)
def cached_airlabs(flight_number, api_key):
    return airlabs_flight(flight_number, api_key=api_key)

@st.cache_data(ttl=300, show_spinner=False)
def cached_opensky(airport):
    latitude, longitude, _ = AIRPORTS[airport]
    return opensky_near_airport(latitude, longitude)

@st.cache_data(ttl=1800, show_spinner=False)
def cached_weather(airport, travel_date):
    latitude, longitude, _ = AIRPORTS[airport]
    return fetch_hourly_forecast(latitude, longitude, travel_date)

def airlabs_key():
    try:
        return st.secrets.get("AIRLABS_API_KEY") or os.getenv("AIRLABS_API_KEY")
    except Exception:
        return os.getenv("AIRLABS_API_KEY")

if submitted:
    try:
        features = build_features(flight, origin, destination, datetime.combine(travel_date, travel_time))
        paths = [ROOT / 'ml' / f'{name}_demo.joblib' for name in ('departure', 'arrival')]
        if not all(p.exists() for p in paths):
            from ml.train import train_demo
            with st.spinner('Preparing demonstration models for first use...'):
                train_demo()
        if all(p.exists() for p in paths):
            scores = [float(joblib.load(path).predict_proba(pd.DataFrame([features])[FEATURES])[0, 1]) for path in paths]
            st.subheader('Prediction results · Synthetic demo')
            x, y = st.columns(2)
            for container, title, score in zip((x, y), ('Departure delay risk', 'Arrival delay risk'), scores):
                with container:
                    st.metric(title, f'{score:.0%}')
                    st.progress(score)
                    st.caption('Illustrative model score only; not a calibrated real-world probability.')

            st.subheader('Aviation data · Live source checks')
            st.caption('Data feeds are separate from synthetic predictions. Current flight status does not establish a verified future flight schedule.')
            flight_data = cached_airlabs(flight, airlabs_key())
            if flight_data['status'] == 'not_configured':
                st.info('AirLabs not connected: add AIRLABS_API_KEY to Streamlit Secrets.')
            elif flight_data['status'] == 'ok':
                matching = flight_matches_route(flight_data['flights'], origin, destination)
                st.success(f"AirLabs: {len(flight_data['flights'])} current record(s) found; {len(matching)} match this route.")
                if matching:
                    st.dataframe(pd.DataFrame(matching), use_container_width=True, hide_index=True)
                else:
                    st.info('No current AirLabs record confirms your selected route.')
            else:
                st.info(f"AirLabs: {flight_data['message']}. This does not imply cancellation.")

            oc1, oc2 = st.columns(2)
            for column, airport, label in ((oc1, origin, 'Departure'), (oc2, destination, 'Arrival')):
                with column:
                    nearby = cached_opensky(airport)
                    if nearby['status'] == 'ok':
                        st.metric(f'OpenSky near {airport}', len(nearby['aircraft']))
                        st.caption('Nearby tracked aircraft right now; not a match to the entered flight.')
                    else:
                        st.info(f'OpenSky {label.lower()} area currently unavailable.')

            st.subheader('Airport weather · Open-Meteo')
            st.caption('Forecast at the entered departure time, shown for both airports. Not used by the synthetic ML models.')
            wc1, wc2 = st.columns(2)
            for column, airport in ((wc1, origin), (wc2, destination)):
                with column:
                    st.markdown(f'**{airport} weather**')
                    try:
                        hourly = cached_weather(airport, travel_date)
                        conditions = weather_at_hour(hourly, datetime.combine(travel_date, travel_time))
                        for label, value in conditions.items():
                            st.write(f"{label}: {value if value is not None else 'Unavailable'}")
                    except (requests.RequestException, ValueError, KeyError, IndexError):
                        st.info('Weather forecast unavailable for this airport and time.')

            st.markdown(f'<div class="ap-panel"><b>{flight.upper()}</b> · {origin} → {destination}<br><span class="ap-warn">Delay means 15+ minutes after the scheduled time. No actual flight schedule was checked.</span></div>', unsafe_allow_html=True)
    except ValueError as exc:
        st.error(str(exc))

with st.expander('About data quality and model readiness'):
    st.write('The included models learn from generated demonstration rows. For real predictions we need legally usable historical flight records, schedule snapshots, a time-based evaluation split, and measured calibration. AirLabs live flight observations, OpenSky nearby aircraft, and Open-Meteo weather integrations are included but do not train or inform the demo model.')
    st.write('The flight number is validated for airline prefixes. AirLabs may provide live records when available, but this app does not validate a future timetable.')

st.caption('AeroPulse · Portfolio prototype · Built with Streamlit and scikit-learn')
