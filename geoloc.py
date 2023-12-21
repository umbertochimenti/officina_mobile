from geopy import distance
from geopy.geocoders import Nominatim
from geopy.distance import geodesic as GD

loc = None
car_workshop_coords = None

def init_geolocalize():
    global loc, car_workshop_coords
    loc = Nominatim(user_agent="Geopy Library")
    car_workshop_coords = (40.64038085651474, 14.847294381362609)

def get_geocode_object(address):
    global loc
    return loc.geocode(address, timeout=4)

def get_full_address(geocode_object):
    return geocode_object.address

def get_lat_lon(geocode_object):
    geo_coords = (geocode_object.latitude, geocode_object.longitude)
    return geo_coords

def get_linear_distance_in_km(start, end):
    return round(GD(start, end).km,2)


# init_geolocalize()
# address = 'Sammichele di bari, bari, italia'
# a = get_geocode_object(address)
# get_lat_lon(a)
