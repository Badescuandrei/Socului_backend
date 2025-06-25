from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from .models import StoreLocation

def geocode_address(address_str):
    """Converts a street address string into latitude and longitude."""
    # It's good practice to initialize the geolocator once if this were a class,
    # but for a simple function, this is fine.
    geolocator = Nominatim(user_agent="socului_restaurant_app_v1")
    try:
        location = geolocator.geocode(address_str, timeout=10) # Added timeout
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        # It's good to log this error in a real application
        print(f"Geocoding error: {e}")
    return None, None

def find_nearest_store(latitude, longitude):
    """
    Finds the nearest active store to a given lat/lon and checks if it's in range.
    
    Returns a tuple: (StoreLocation object, distance in km, can_deliver boolean)
    """
    if not latitude or not longitude:
        return None, None, False

    user_location = (latitude, longitude)
    active_stores = StoreLocation.objects.filter(is_active=True)
    
    if not active_stores.exists():
        return None, None, False

    # Find the closest store using a generator expression for efficiency
    closest_store = min(
        active_stores,
        key=lambda store: great_circle(user_location, (store.latitude, store.longitude)).km
    )

    distance_km = great_circle(user_location, (closest_store.latitude, closest_store.longitude)).km

    # Check if the user is within the delivery radius of that closest store
    can_deliver = distance_km <= closest_store.delivery_radius_km

    return closest_store, distance_km, can_deliver