import random
from typing import List
import requests
from urllib.parse import quote


class CuisineSelector:
    """Handles cuisine selection and restaurant discovery"""
    
    CUISINES = ["Thai", "Chinese", "Indian"]
    
    def __init__(self):
        self.last_selected_cuisine = None
        self.used_restaurants = set()
    
    def select_random_cuisine(self) -> str:
        """Select a random cuisine from the available options"""
        cuisine = random.choice(self.CUISINES)
        self.last_selected_cuisine = cuisine
        return cuisine
    
    def search_restaurants(self, cuisine: str, location: str, day: str, 
                          time: str, party_size: int) -> List[dict]:
        """
        Search for restaurants using web search
        Returns a list of restaurant candidates
        """
        # Construct search query
        search_query = f"{cuisine} restaurants {location} {day} {time} for {party_size}"
        
        try:
            # This is a simplified search - in a real implementation, you might use
            # Google Places API, Yelp API, or a web search API
            return self._mock_restaurant_search(cuisine, location, party_size)
        except Exception as e:
            print(f"Error searching restaurants: {e}")
            return self._get_fallback_restaurants(cuisine, location)
    
    def _mock_restaurant_search(self, cuisine: str, location: str, party_size: int) -> List[dict]:
        """Mock restaurant search results for demonstration"""
        
        restaurant_data = {
            "Thai": [
                {
                    "name": "Thai Garden Restaurant",
                    "address": "123 Market St, San Francisco, CA",
                    "phone": "(415) 555-0123",
                    "rating": 4.5,
                    "price_range": "$$",
                    "opentable_url": "https://www.opentable.com/r/thai-garden-san-francisco"
                },
                {
                    "name": "Golden Thai Cuisine",
                    "address": "456 Union Square, San Francisco, CA", 
                    "phone": "(415) 555-0456",
                    "rating": 4.3,
                    "price_range": "$$$",
                    "opentable_url": "https://www.opentable.com/r/golden-thai-san-francisco"
                },
                {
                    "name": "Spice House Thai",
                    "address": "789 Mission St, San Francisco, CA",
                    "phone": "(415) 555-0789",
                    "rating": 4.2,
                    "price_range": "$$",
                    "opentable_url": "https://www.opentable.com/r/spice-house-thai-sf"
                }
            ],
            "Chinese": [
                {
                    "name": "Dragon Palace",
                    "address": "321 Chinatown, San Francisco, CA",
                    "phone": "(415) 555-1234",
                    "rating": 4.6,
                    "price_range": "$$$",
                    "opentable_url": "https://www.opentable.com/r/dragon-palace-sf"
                },
                {
                    "name": "Golden Dragon Restaurant", 
                    "address": "654 Grant Ave, San Francisco, CA",
                    "phone": "(415) 555-5678",
                    "rating": 4.4,
                    "price_range": "$$",
                    "opentable_url": "https://www.opentable.com/r/golden-dragon-sf"
                },
                {
                    "name": "Jade Garden Chinese",
                    "address": "987 Stockton St, San Francisco, CA",
                    "phone": "(415) 555-9876",
                    "rating": 4.1,
                    "price_range": "$$",
                    "opentable_url": "https://www.opentable.com/r/jade-garden-sf"
                }
            ],
            "Indian": [
                {
                    "name": "Taj Mahal Indian Cuisine",
                    "address": "159 Folsom St, San Francisco, CA",
                    "phone": "(415) 555-1590",
                    "rating": 4.7,
                    "price_range": "$$$",
                    "opentable_url": "https://www.opentable.com/r/taj-mahal-sf"
                },
                {
                    "name": "Spice Route Indian",
                    "address": "357 Valencia St, San Francisco, CA",
                    "phone": "(415) 555-3570",
                    "rating": 4.3,
                    "price_range": "$$",
                    "opentable_url": "https://www.opentable.com/r/spice-route-sf"
                },
                {
                    "name": "Mumbai Palace",
                    "address": "741 Mission St, San Francisco, CA",
                    "phone": "(415) 555-7410",
                    "rating": 4.2,
                    "price_range": "$$",
                    "opentable_url": "https://www.opentable.com/r/mumbai-palace-sf"
                }
            ]
        }
        
        return restaurant_data.get(cuisine, [])
    
    def _get_fallback_restaurants(self, cuisine: str, location: str) -> List[dict]:
        """Fallback restaurants if search fails"""
        fallback = {
            "Thai": {
                "name": "Local Thai Restaurant",
                "address": f"Downtown {location}",
                "phone": "(555) 123-4567",
                "rating": 4.0,
                "price_range": "$$",
                "opentable_url": "https://www.opentable.com"
            },
            "Chinese": {
                "name": "Local Chinese Restaurant", 
                "address": f"Downtown {location}",
                "phone": "(555) 234-5678",
                "rating": 4.0,
                "price_range": "$$",
                "opentable_url": "https://www.opentable.com"
            },
            "Indian": {
                "name": "Local Indian Restaurant",
                "address": f"Downtown {location}",
                "phone": "(555) 345-6789", 
                "rating": 4.0,
                "price_range": "$$",
                "opentable_url": "https://www.opentable.com"
            }
        }
        
        return [fallback.get(cuisine, fallback["Thai"])]
    
    def select_restaurant(self, restaurants: List[dict]) -> dict:
        """
        Select a restaurant using the simple rule:
        First viable result that isn't a duplicate from the last run
        """
        if not restaurants:
            return None
        
        # Try to find a restaurant we haven't used recently
        for restaurant in restaurants:
            restaurant_key = f"{restaurant['name']}_{restaurant.get('address', '')}"
            if restaurant_key not in self.used_restaurants:
                self.used_restaurants.add(restaurant_key)
                # Keep only the last 10 used restaurants to allow reuse eventually
                if len(self.used_restaurants) > 10:
                    # Remove the oldest entry (simplified approach)
                    self.used_restaurants.pop()
                return restaurant
        
        # If all restaurants have been used recently, just pick the first one
        restaurant = restaurants[0]
        restaurant_key = f"{restaurant['name']}_{restaurant.get('address', '')}"
        self.used_restaurants.add(restaurant_key)
        return restaurant
    
    def get_restaurant_recommendation(self, location: str, day: str, time: str, 
                                    party_size: int) -> tuple:
        """
        Complete flow: select cuisine, search restaurants, pick one
        Returns (cuisine, restaurant_info)
        """
        # Select random cuisine
        cuisine = self.select_random_cuisine()
        
        # Search for restaurants
        restaurants = self.search_restaurants(cuisine, location, day, time, party_size)
        
        # Select best restaurant
        selected_restaurant = self.select_restaurant(restaurants)
        
        return cuisine, selected_restaurant
