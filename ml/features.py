"""Shared feature logic for model training and inference."""
from datetime import datetime

AIRPORTS = {
    'DEL': (28.5562, 77.1000, 'Delhi'),
    'BOM': (19.0896, 72.8656, 'Mumbai'),
    'HYD': (17.2403, 78.4294, 'Hyderabad'),
    'BLR': (13.1986, 77.7066, 'Bengaluru'),
    'MAA': (12.9941, 80.1709, 'Chennai'),
    'CCU': (22.6547, 88.4467, 'Kolkata'),
    'PNQ': (18.5821, 73.9197, 'Pune'),
    'GOI': (15.3808, 73.8314, 'Goa'),
}
AIRLINES = {'6E': 'IndiGo', 'AI': 'Air India', 'QP': 'Akasa Air', 'IX': 'Air India Express'}
FEATURES = ['airline_code', 'origin_code', 'destination_code', 'month', 'day_of_week', 'departure_hour']


def build_features(flight_number: str, origin: str, destination: str, scheduled_departure: datetime):
    flight_number = flight_number.strip().upper().replace(' ', '')
    prefix = next((code for code in sorted(AIRLINES, key=len, reverse=True) if flight_number.startswith(code)), None)
    if not prefix or not flight_number[len(prefix):].isdigit():
        raise ValueError('Use a supported flight number such as 6E203, AI501, QP1102 or IX123.')
    if origin not in AIRPORTS or destination not in AIRPORTS or origin == destination:
        raise ValueError('Choose two different supported airports.')
    return {'airline_code': prefix, 'origin_code': origin, 'destination_code': destination,
            'month': scheduled_departure.month, 'day_of_week': scheduled_departure.weekday(),
            'departure_hour': scheduled_departure.hour}
