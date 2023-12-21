import requests
import json

# URL di destinazione
url = "https://api.traveltimeapp.com/v4/time-filter"

# Intestazioni della richiesta
headers = {
    'Content-Type': 'application/json',
    'X-Application-Id': 'dd2a6475',
    'X-Api-Key': 'bc39c684f9235cce13804cb6f117727a'
}

# Dati del corpo della richiesta
data = {
    "locations": [
        {"id": "Via Stefano Da Putignano, Sammichele di Bari (BA), Italy", "coords": {"lat": 40.8928601, "lng": 16.9536356}},
        {"id": "Via antonio pacinotti, Sammichele di Bari (BA), Italy", "coords": {"lat": 40.8863534, "lng": 16.9491339}},
        {"id": "Via roma, 1, Sammichele di Bari (BA), Italy", "coords": {"lat": 40.8880389, "lng": 16.9460158}},
        {"id": "Turi (BA), Italy", "coords": {"lat": 40.917331, "lng": 17.021191}},
        {"id": "Cassano delle murge (BA), Italy", "coords": {"lat": 40.8910105, "lng": 16.7686188}}
    ],
    "departure_searches": [
        {
            "id": "One-to-many-Matrix",
            "departure_location_id": "Via Stefano Da Putignano, Sammichele di Bari (BA), Italy",
            "arrival_location_ids": [
                "Via antonio pacinotti, Sammichele di Bari (BA), Italy",
                "Via roma, 1, Sammichele di Bari (BA), Italy",
                "Turi (BA), Italy",
                "Cassano delle murge (BA), Italy"
            ],
            "departure_time": "2022-09-21T08:00:00Z",
            "travel_time": 3600,
            "properties": ["travel_time", "distance"],
            "transportation": {"type": "driving"}
        }
    ]
}

# Effettua la richiesta POST
response = requests.post(url, headers=headers, data=json.dumps(data))

# Stampa la risposta
print(response.status_code)
print(response.json())

