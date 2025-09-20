"""Constants for the FatSecret custom component."""

DOMAIN = "fatsecret"
SENSOR_TYPES = {
    "calories": "Calories",
    "carbs": "Carbohydrate",
    "protein": "Protein",
    "fat": "Fat",
    "fiber": "Fiber",
    "sugar": "Sugar",
}


CONF_CONSUMER_KEY = "consumer_key"
CONF_CONSUMER_SECRET = "consumer_secret"
CONF_TOKEN = "token"
CONF_TOKEN_SECRET = "token_secret"

REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
AUTHORIZE_URL = "https://authentication.fatsecret.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
API_BASE_URL = "https://platform.fatsecret.com/rest/"
API_FOOD_ENTRIES_URL = API_BASE_URL + "food-entries/v2"
OAUTH_VERSION = "1.0"
OAUTH_SIGNATURE_METHOD = "HMAC-SHA1"
