import asyncio
from traveltimepy import TravelTimeSdk
import requests
import json
from datetime import datetime, timezone

app_id = "xxxxxxxx"
api_key = "xyzxyzxyzxyzxyzxyzxyzxyzxyz"

car_workshop_coords = (40.64038085651474, 14.847294381362609)

async def address_to_coords(address):    
    sdk = TravelTimeSdk(app_id, api_key)
    results = await sdk.geocoding_async(query=address, limit=30)
    address = address.replace("'", " ")
    loc = {"id":address, "coords": {"lat": None, "lng": None}}
    if len(results.features) > 0:
        loc['coords']['lng'] = results.features[0].geometry.coordinates[0]
        loc['coords']['lat'] = results.features[0].geometry.coordinates[1]
    return loc

def create_travel_time_matrix_from_A_to_all(locations):
    travel_time_matrix = {"locations": locations, "departure_searches": None}
    departure_searches = []
    arrival_location_ids = []
    for i, loc in enumerate(locations):
        if i > 0:
            arrival_location_ids.append(loc['id'])

    if len(locations) > 1:
        locations_object = {"locations": locations}
        now = datetime.now(timezone.utc)
        formatted_datetime = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        departure_search = {
                            "id": "FROM: " + str(locations[0]['id']), 
                            "departure_location_id": locations[0]['id'], 
                            "arrival_location_ids": arrival_location_ids,
                            "departure_time": str(formatted_datetime),
                            "travel_time": 14400,
                            "properties": ["travel_time","distance"],
                            "transportation": {"type": "driving"}
                            }
        departure_searches.append(departure_search)
        travel_time_matrix['departure_searches']=departure_searches

    return travel_time_matrix

def get_travel_time_matrix(travel_time_matrix):
    url = "https://api.traveltimeapp.com/v4/time-filter"
    headers = {
        'Content-Type': 'application/json',
        'X-Application-Id': app_id,
        'X-Api-Key': api_key
    }

    response = requests.post(url, headers=headers, data=json.dumps(travel_time_matrix))
    print(response.status_code)
    print(response.json())
    return response.json()
    

locations = []
address = "Via Stefano Da Putignano, Sammichele di Bari (BA), Italy"
coords = asyncio.run(address_to_coords(address))
locations.append(coords)
print(coords)
address = "Via antonio pacinotti, Sammichele di Bari (BA), Italy"
coords = asyncio.run(address_to_coords(address))
locations.append(coords)

address = "Via roma, 1, Sammichele di Bari (BA), Italy"
coords = asyncio.run(address_to_coords(address))
locations.append(coords)

address = "Turi (BA), Italy"
coords = asyncio.run(address_to_coords(address))
locations.append(coords)

address = "Cassano delle murge (BA), Italy"
coords = asyncio.run(address_to_coords(address))
locations.append(coords)

travel_time_matrix = create_travel_time_matrix_from_A_to_all(locations)
print(json.dumps(travel_time_matrix, indent=2))
get_travel_time_matrix(travel_time_matrix)
