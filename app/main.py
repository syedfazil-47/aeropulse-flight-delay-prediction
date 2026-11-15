"""AeroPulse: India domestic flight-delay demo dashboard."""
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.features import AIRPORTS, AIRLINES, FEATURES, build_features

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
st.warning('DEMO MODE — predictions use synthetic training data, not verified airline schedules or live operational data. Do not use for travel decisions.')

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
            st.markdown(f'<div class="ap-panel"><b>{flight.upper()}</b> · {origin} → {destination}<br><span class="ap-warn">Delay means 15+ minutes after the scheduled time. No actual flight schedule was checked.</span></div>', unsafe_allow_html=True)
    except ValueError as exc:
        st.error(str(exc))

with st.expander('About data quality and model readiness'):
    st.write('The included models learn from generated demonstration rows. For real predictions we need legally usable historical flight records, schedule snapshots, a time-based evaluation split, and measured calibration. Live flight API and weather integration are planned, not yet connected.')
    st.write('The flight number is validated for supported airline prefixes but is not looked up in an airline timetable.')

st.caption('AeroPulse · Portfolio prototype · Built with Streamlit and scikit-learn')
