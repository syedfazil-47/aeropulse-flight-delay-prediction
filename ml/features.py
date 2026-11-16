"""Shared feature logic for model training and inference."""
from datetime import datetime

# Airport coordinates are approximate reference positions for weather and tracking,
# not airport operating details, airline timetables or availability guarantees.
AIRPORTS = {
    'DEL': (28.5562, 77.1000, 'Delhi'),
    'BOM': (19.0896, 72.8656, 'Mumbai'),
    'HYD': (17.2403, 78.4294, 'Hyderabad'),
    'BLR': (13.1986, 77.7066, 'Bengaluru'),
    'MAA': (12.9941, 80.1709, 'Chennai'),
    'CCU': (22.6547, 88.4467, 'Kolkata'),
    'PNQ': (18.5821, 73.9197, 'Pune'),
    'GOI': (15.3808, 73.8314, 'Goa (Dabolim)'),
    'GOX': (15.7443, 73.8606, 'Goa (Manohar)'),
    'AMD': (23.0772, 72.6347, 'Ahmedabad'),
    'COK': (10.1520, 76.4019, 'Kochi'),
    'TRV': (8.4821, 76.9201, 'Thiruvananthapuram'),
    'CCJ': (11.1368, 75.9553, 'Kozhikode'),
    'CJB': (11.0300, 77.0434, 'Coimbatore'),
    'IXM': (9.8345, 78.0934, 'Madurai'),
    'TRZ': (10.7654, 78.7097, 'Tiruchirappalli'),
    'VTZ': (17.7212, 83.2245, 'Visakhapatnam'),
    'VGA': (16.5304, 80.7968, 'Vijayawada'),
    'TIR': (13.6325, 79.5433, 'Tirupati'),
    'BBI': (20.2444, 85.8178, 'Bhubaneswar'),
    'PAT': (25.5913, 85.0880, 'Patna'),
    'LKO': (26.7606, 80.8893, 'Lucknow'),
    'VNS': (25.4524, 82.8593, 'Varanasi'),
    'JAI': (26.8242, 75.8122, 'Jaipur'),
    'UDR': (24.6177, 73.8961, 'Udaipur'),
    'JDH': (26.2511, 73.0489, 'Jodhpur'),
    'ATQ': (31.7096, 74.7973, 'Amritsar'),
    'SXR': (33.9871, 74.7742, 'Srinagar'),
    'IXJ': (32.6891, 74.8374, 'Jammu'),
    'IXC': (30.6735, 76.7885, 'Chandigarh'),
    'DED': (30.1897, 78.1803, 'Dehradun'),
    'IXB': (26.6812, 88.3286, 'Bagdogra'),
    'GAU': (26.1061, 91.5859, 'Guwahati'),
    'IMF': (24.7600, 93.8967, 'Imphal'),
    'IXA': (23.8869, 91.2405, 'Agartala'),
    'DIB': (27.4839, 95.0169, 'Dibrugarh'),
    'RPR': (21.1804, 81.7388, 'Raipur'),
    'NAG': (21.0922, 79.0472, 'Nagpur'),
    'IDR': (22.7218, 75.8011, 'Indore'),
    'BHO': (23.2875, 77.3374, 'Bhopal'),
    'STV': (21.1141, 72.7418, 'Surat'),
    'BDQ': (22.3362, 73.2263, 'Vadodara'),
    'IXE': (12.9613, 74.8901, 'Mangaluru'),
}
AIRLINES = {
    '6E': 'IndiGo', 'AI': 'Air India', 'QP': 'Akasa Air',
    'IX': 'Air India Express', 'SG': 'SpiceJet',
    '9I': 'Alliance Air', 'S5': 'Star Air', 'IC': 'FLY91',
}
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
