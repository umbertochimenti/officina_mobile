curl -X POST https://api.traveltimeapp.com/v4/time-filter \
-H 'Content-Type: application/json' \
-H 'X-Application-Id: dd2a6475' \
-H 'X-Api-Key: bc39c684f9235cce13804cb6f117727a' \
-d '{
  "locations": [
    {
      "id": "OFFICINA",
      "coords": {
        "lat": 40.64038085651474,
        "lng": 14.847294381362609
      }
    },
    {
      "id": "VIA DEI MILLE, 3, SALERNO, ITALIA",
      "coords": {
        "lat": 40.6670494,
        "lng": 14.7991823
      }
    },
    {
      "id": "VIA MADONNA DELL ETERNO, 17, BELLIZZI, ITALIA",
      "coords": {
        "lat": 40.6214716,
        "lng": 14.9464717
      }
    }
  ],
  "departure_searches": [
    {
      "id": "FROM: OFFICINA",
      "departure_location_id": "OFFICINA",
      "arrival_location_ids": [
        "VIA DEI MILLE, 3, SALERNO, ITALIA",
        "VIA MADONNA DELL ETERNO, 17, BELLIZZI, ITALIA"
      ],
      "departure_time": "2022-09-21T08:00:00Z",
      "travel_time": 3600,
      "properties": [
        "travel_time",
        "distance"
      ],
      "transportation": {
        "type": "driving"
      }
    }
  ]
}'
