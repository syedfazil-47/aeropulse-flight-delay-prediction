"""AeroPulse — bright, flight-first aviation intelligence dashboard."""
from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path
import importlib.util
import os
import sys

import joblib
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.features import AIRPORTS, AIRLINES, FEATURES, build_features

def load_local(name, filename):
    path = ROOT / "integrations" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("AeroPulse integration file is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

aviation = load_local("aeropulse_aviation", "aviation.py")
weather = load_local("aeropulse_weather", "weather.py")
flightlib = load_local("aeropulse_flight_profile", "flight_profile.py")

st.set_page_config(
    page_title="AeroPulse | Flight Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown("""
<style>
:root {--ink:#102d4d;--sky:#087bc4;--teal:#06a8bd;--muted:#58738c;--line:#dce8f2}
.stApp {background:linear-gradient(180deg,#eef8ff 0%,#fff 290px,#f7fbff 100%);color:#102d4d}
[data-testid="stHeader"] {background:transparent}
.block-container {max-width:1320px;padding-top:1.9rem;padding-bottom:3rem}
h1,h2,h3 {color:#123556!important;letter-spacing:-.025em}
p,li {color:#344c62}
[data-testid="stWidgetLabel"] p {color:#163953!important;font-weight:650!important}
[data-testid="stForm"] {background:#fff!important;border:1px solid #d9e8f4!important;
border-radius:22px!important;padding:22px!important;box-shadow:0 14px 42px rgba(21,80,125,.07)}
[data-testid="stMetric"] {background:#fff!important;border:1px solid #e0edf6;
border-radius:16px;padding:15px}
[data-testid="stMetricLabel"] p {color:#657d91!important;font-weight:600!important}
[data-testid="stMetricValue"] {color:#0f588c!important}
[data-testid="stFormSubmitButton"] button {background:linear-gradient(100deg,#0679ca,#02b1c1)!important;
color:#fff!important;font-weight:800!important;border:0!important;border-radius:12px!important;
min-height:49px;box-shadow:0 8px 22px rgba(0,122,197,.19)}
[data-testid="stFormSubmitButton"] button:hover {filter:brightness(.96)}
[data-testid="stSelectbox"]>div,[data-testid="stTextInput"]>div {border-radius:10px}
.ap-top {display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:28px}
.ap-logo {display:flex;align-items:center;gap:10px;color:#103c65;font-size:25px;font-weight:850;letter-spacing:-.04em}
.ap-mark {background:linear-gradient(125deg,#0578c7,#16c4ce);color:white;border-radius:14px;
width:42px;height:42px;display:flex;align-items:center;justify-content:center}
.ap-topright {font-size:12px;font-weight:750;color:#147aa4;letter-spacing:1.5px}
.ap-hero {background:linear-gradient(115deg,#076fb0,#0aa7c1);border-radius:26px;
padding:38px 42px;margin:0 0 25px;color:#fff;box-shadow:0 18px 42px rgba(8,103,167,.19);position:relative;overflow:hidden}
.ap-hero:after {content:'✈';position:absolute;font-size:190px;right:25px;top:-55px;
color:rgba(255,255,255,.11);transform:rotate(-14deg)}
.ap-kicker {font-size:12px;font-weight:800;letter-spacing:2.4px;color:#c3f5ff}
.ap-hero h1 {font-size:clamp(29px,4.1vw,51px)!important;line-height:1.12;
margin:12px 0!important;color:white!important;max-width:760px}
.ap-hero p {color:#e1f8ff;font-size:16px;max-width:670px;margin:0}
.ap-section {margin:30px 0 12px;font-size:20px;font-weight:800;color:#163c61}
.ap-panel {background:white;border:1px solid #dceaf3;border-radius:20px;padding:22px 25px;
box-shadow:0 8px 32px rgba(16,70,107,.045);margin-bottom:16px}
.ap-overline {font-size:11px;font-weight:850;color:#5482a4;letter-spacing:1.5px;text-transform:uppercase}
.ap-flightline {font-size:21px;font-weight:850;color:#153d5f;margin-top:7px}
.ap-route {display:flex;align-items:center;justify-content:space-between;gap:12px;margin:19px 0;flex-wrap:wrap}
.ap-airport {font-size:clamp(28px,5vw,49px);font-weight:850;color:#073a65;letter-spacing:-2px}
.ap-city {color:#536e84;font-weight:600;font-size:13px}
.ap-dashes {flex:1;min-width:70px;text-align:center;color:#079fc2;font-size:22px;
border-bottom:2px dashed #abdae8;padding-bottom:10px}
.ap-pill {display:inline-block;background:#e7f7fb;color:#06748d;font-size:11px;
font-weight:800;padding:5px 10px;border-radius:100px;margin:5px 5px 0 0}
.ap-pill-muted {background:#edf2f6;color:#657d90}
.ap-notice {font-size:12px;color:#59778f;line-height:1.5}
.ap-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:16px}
.ap-kpi {background:#f4faff;border:1px solid #e0eef8;border-radius:13px;padding:14px}
.ap-kpi strong {font-size:14px;display:block;color:#133f60;margin-top:5px;overflow-wrap:anywhere}
.ap-kpi small {color:#62819c;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.6px}
.ap-footer {color:#6a859a;font-size:11px;margin-top:25px}
@media(max-width:700px) {
.block-container {padding-left:1rem;padding-right:1rem;padding-top:1.15rem}
.ap-hero {padding:25px 21px;border-radius:20px}
.ap-hero:after {font-size:110px;top:0;right:-5px}
.ap-panel {padding:18px 16px}
.ap-grid {grid-template-columns:repeat(2,minmax(0,1fr))}
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ap-top">
  <div class="ap-logo"><span class="ap-mark">✈</span>AeroPulse</div>
  <div class="ap-topright">INDIA · FLIGHT INTELLIGENCE</div>
</div>
<div class="ap-hero">
  <div class="ap-kicker">FLIGHT INTELLIGENCE, REIMAGINED</div>
  <h1>Know your flight.<br>Travel with clarity.</h1>
  <p>Explore Indian airline flights, verified information where available,
  airport weather and experimental delay-risk insights.</p>
</div>
""", unsafe_allow_html=True)

def secret(key):
    try:
        return st.secrets.get(key) or os.getenv(key)
    except Exception:
        return os.getenv(key)

@st.cache_data(ttl=600, show_spinner=False)
def live_flight_lookup(number, _key):
    return aviation.airlabs_flight(number, api_key=_key)

@st.cache_data(ttl=1800, show_spinner=False)
def airport_weather(code, selected_date):
    lat,lon,_=AIRPORTS[code]
    return weather.fetch_hourly_forecast(lat,lon,selected_date)

@st.cache_data(ttl=300, show_spinner=False)
def aircraft_count(code):
    lat,lon,_=AIRPORTS[code]
    return aviation.adsb_lol_near_airport(lat,lon)

@st.cache_resource(show_spinner=False)
def models():
    paths=[ROOT/"ml"/f"{name}_demo.joblib" for name in ("departure","arrival")]
    if not all(path.exists() for path in paths):
        from ml.train import train_demo
        train_demo()
    return [joblib.load(path) for path in paths]

def donut(score, heading, accent):
    score=max(0,min(1,score))
    fig=go.Figure(go.Pie(
        labels=["Delay 15+ min","On time / under 15 min"],
        values=[round(score*100,1),round((1-score)*100,1)],
        hole=.77, sort=False, direction="clockwise",
        marker=dict(colors=[accent,"#e7f0f7"],line=dict(color="#fff",width=2)),
        textinfo="none", hovertemplate="%{label}: %{value:.0f}%<extra></extra>",
        showlegend=False,
    ))
    fig.add_annotation(text=f"<b>{score:.0%}</b><br><span style='font-size:12px;color:#6b8297'>risk</span>",
                       x=.5,y=.5,showarrow=False,font=dict(size=30,color="#113f62"))
    fig.update_layout(height=235,margin=dict(l=0,r=0,t=7,b=0),paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial"),showlegend=False)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown(f"<div style='text-align:center;font-weight:800;color:#164362'>{escape(heading)}</div>"
                f"<div style='text-align:center;font-size:12px;color:#6b8297'>"
                f"Illustrative on-time share: {(1-score):.0%}</div>",unsafe_allow_html=True)

st.markdown('<div class="ap-section">Find your flight</div>',unsafe_allow_html=True)
with st.form("lookup"):
    a,b,c=st.columns([1.2,1,1])
    flight=a.text_input("Flight number",value="",placeholder="e.g. 6E 203",
                        help="Supported prototype airlines: IndiGo, Air India, Akasa, Air India Express")
    flight_date=b.date_input("Travel date",value=date.today(),
                             min_value=date.today(),max_value=date.today()+timedelta(days=7))
    dep_time=c.time_input("Departure time (IST, if known)",time(18,30))
    x,y=st.columns(2)
    choices=list(AIRPORTS)
    origin=x.selectbox("Departure airport (manual fallback)",choices,
                       index=choices.index("HYD"),format_func=lambda k:f"{k} · {AIRPORTS[k][2]}")
    dest=y.selectbox("Arrival airport (manual fallback)",choices,
                     index=choices.index("DEL"),format_func=lambda k:f"{k} · {AIRPORTS[k][2]}")
    submitted=st.form_submit_button("Explore flight intelligence  ✈",type="primary",use_container_width=True)

if submitted:
    normalized=flightlib.normalize_flight(flight)
    try:
        if not normalized:
            raise ValueError("Enter your airline flight number first.")
        if origin==dest:
            raise ValueError("Select different departure and arrival airports.")
        carrier=flightlib.known_carrier(normalized,AIRLINES)
        with st.spinner("Checking flight details and available information..."):
            result=live_flight_lookup(normalized,secret("AIRLABS_API_KEY"))
        verified=flightlib.choose_flight(result.get("flights",[]),normalized,flight_date)
        flight_origin=verified["dep_iata"] if verified else origin
        flight_dest=verified["arr_iata"] if verified else dest
        origin_known=flight_origin in AIRPORTS
        dest_known=flight_dest in AIRPORTS
        city_origin=AIRPORTS[flight_origin][2] if origin_known else "Airport not in directory"
        city_dest=AIRPORTS[flight_dest][2] if dest_known else "Airport not in directory"
        source_msg="Verified matching record · AirLabs" if verified else "User-selected route · Not flight-verified"
        badge_class="" if verified else " ap-pill-muted"
        live_state=verified.get("status") if verified else None
        st.markdown('<div class="ap-section">Your flight overview</div>',unsafe_allow_html=True)
        st.markdown(
            '<div class="ap-panel"><div class="ap-overline">FLIGHT PROFILE · '+escape(flight_date.strftime("%A, %d %B %Y"))+'</div>'
            '<div class="ap-flightline">'+escape(carrier)+' · '+escape(normalized)+'</div>'
            '<span class="ap-pill'+badge_class+'">'+escape(source_msg)+'</span>'
            '<div class="ap-route"><div><div class="ap-airport">'+escape(flight_origin)+'</div>'
            '<div class="ap-city">'+escape(city_origin)+'</div></div>'
            '<div class="ap-dashes">✈</div>'
            '<div style="text-align:right"><div class="ap-airport">'+escape(flight_dest)+'</div>'
            '<div class="ap-city">'+escape(city_dest)+'</div></div></div>'
            '<div class="ap-grid">'
            '<div class="ap-kpi"><small>Flight</small><strong>'+escape(normalized)+'</strong></div>'
            '<div class="ap-kpi"><small>Airline</small><strong>'+escape(carrier)+'</strong></div>'
            '<div class="ap-kpi"><small>Departure</small><strong>'+escape(flightlib.show_time(verified.get("dep_time")) if verified else dep_time.strftime("%H:%M")+' · entered')+'</strong></div>'
            '<div class="ap-kpi"><small>Arrival</small><strong>'+escape(flightlib.show_time(verified.get("arr_time")) if verified else "Not verified")+'</strong></div>'
            '</div></div>',unsafe_allow_html=True)
        if verified:
            if live_state:
                st.caption("AirLabs status: "+str(live_state)+". Provider-reported status, not a guarantee.")
            if verified.get("dep_actual") or verified.get("arr_actual"):
                st.caption("Reported actual departure: "+flightlib.show_time(verified.get("dep_actual"))
                           +" · Actual arrival: "+flightlib.show_time(verified.get("arr_actual")))
            if (origin,dest)!=(flight_origin,flight_dest):
                st.info("Provider-reported route differs from your manual selections. Flight profile uses the provider record.")
        else:
            st.caption("No date-matched, route-confirmed airline record was returned by AirLabs. "
                       "The route and departure time above are your selections, not a verified schedule. "
                       "This does not mean the flight is cancelled.")
            if result.get("status") not in ("ok","not_found"):
                st.caption("AirLabs lookup: "+result.get("message","No provider data available"))
        st.markdown('<div class="ap-section">Delay risk outlook</div>',unsafe_allow_html=True)
        if origin_known and dest_known and carrier!="Carrier not confirmed":
            try:
                model_input=build_features(normalized,flight_origin,flight_dest,
                                          datetime.combine(flight_date,dep_time))
                frame=pd.DataFrame([model_input])[FEATURES]
                with st.spinner("Computing experimental model estimates..."):
                    scores=[float(model.predict_proba(frame)[0,1]) for model in models()]
                st.caption("Experimental model · example-trained · not a validated real-flight forecast")
                p1,p2=st.columns(2)
                with p1:
                    donut(scores[0],"Departure delay","#0b9cd5")
                with p2:
                    donut(scores[1],"Arrival delay","#f39a50")
                st.caption("A delay means 15 minutes or more after schedule. Estimates above come from simulated training examples; "
                           "they are not probabilities calibrated to actual Indian flight operations.")
            except (ValueError,OSError,KeyError) as exc:
                st.info("Experimental risk estimates unavailable for this selection.")
        else:
            st.info("No experimental risk score for this route. Flight information can still be explored.")
        st.markdown('<div class="ap-section">Airport conditions</div>',unsafe_allow_html=True)
        wc1,wc2=st.columns(2)
        for column,airport,city in ((wc1,flight_origin,city_origin),(wc2,flight_dest,city_dest)):
            with column:
                st.markdown(f"**{escape(city)} · {escape(airport)}**")
                if airport not in AIRPORTS:
                    st.caption("Weather data unavailable for this airport.")
                    continue
                try:
                    current=weather.weather_at_hour(airport_weather(airport,flight_date),
                                                     datetime.combine(flight_date,dep_time))
                    temp=current.get("Temperature (°C)")
                    rain=current.get("Rain chance (%)")
                    wind=current.get("Wind (km/h)")
                    st.metric("Temperature",f"{temp}°C" if temp is not None else "—")
                    st.caption(f"Rain chance: {rain if rain is not None else '—'}% · Wind: {wind if wind is not None else '—'} km/h")
                except (requests.RequestException,ValueError,KeyError,IndexError):
                    st.caption("Forecast unavailable for the selected hour.")
        st.caption("Weather refers to the selected departure hour at each airport, not the actual arrival hour.")
        with st.expander("Nearby aircraft activity · optional"):
            st.caption("Community ADS-B observations near each airport (adsb.lol, ODbL 1.0). "
                       "Nearby planes are not necessarily the searched flight.")
            n1,n2=st.columns(2)
            for column,airport in ((n1,flight_origin),(n2,flight_dest)):
                with column:
                    if airport not in AIRPORTS:
                        continue
                    info=aircraft_count(airport)
                    if info["status"]=="ok":
                        st.metric(f"Near {airport}",len(info["aircraft"]))
                    else:
                        st.caption(f"{airport}: tracking unavailable ({info['status']})")
        with st.expander("How AeroPulse sources and evaluates data"):
            st.write("AirLabs provides current flight observations when covered by the API plan. "
                     "Flights are only labeled date-verified when their flight number, date, "
                     "and both airport codes match. Open-Meteo provides weather forecasts. "
                     "Community ADS-B data describes nearby aircraft only.")
            st.write("The delay classifier is a portfolio demonstration trained with generated examples. "
                     "Real prediction accuracy cannot be claimed until sufficient legally usable "
                     "historical Indian airline records are collected and evaluated chronologically.")
    except ValueError as exc:
        st.error(str(exc))

st.markdown('<div class="ap-footer">AeroPulse · Indian aviation intelligence prototype · Flight information depends on provider coverage. '
            'Always confirm schedules with the airline.</div>',unsafe_allow_html=True)
