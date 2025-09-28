"""Constants for the FatSecret custom component."""

DOMAIN = "fatsecret"

CONF_CONSUMER_KEY = "consumer_key"
CONF_CONSUMER_SECRET = "consumer_secret"
CONF_TOKEN = "token"
CONF_TOKEN_SECRET = "token_secret"

REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
AUTHORIZE_URL = "https://authentication.fatsecret.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
API_BASE_URL = "https://platform.fatsecret.com/rest/"
API_FOOD_ENTRIES_URL = API_BASE_URL + "food-entries/v2"

OAUTH_PARAM_CONSUMER_KEY = "oauth_consumer_key"
OAUTH_PARAM_TOKEN = "oauth_token"
OAUTH_PARAM_SIGNATURE = "oauth_signature"
OAUTH_PARAM_SIGNATURE_METHOD = "oauth_signature_method"
OAUTH_PARAM_TIMESTAMP = "oauth_timestamp"
OAUTH_PARAM_NONCE = "oauth_nonce"
OAUTH_PARAM_VERSION = "oauth_version"
OAUTH_PARAM_CALLBACK = "oauth_callback"
OAUTH_PARAM_VERIFIER = "oauth_verifier"
OAUTH_PARAM_TOKEN_SECRET = "oauth_token_secret"

OAUTH_VERSION = "1.0"
OAUTH_SIGNATURE_METHOD = "HMAC-SHA1"
OAUTH_CALLBACK = "oob"  # out-of-band, user will copy-paste verifier

FATSECRET_FOOD_ENTRIES = "food_entries"
FATSECRET_FOOD_ENTRY = "food_entry"
FATSECRET_FIELDS = {
    "calories": {"unit": "kcal", "name": "Calories"},
    "carbohydrate": {"unit": "g", "name": "Carbohydrates"},
    "protein": {"unit": "g", "name": "Protein"},
    "fat": {"unit": "g", "name": "Fat"},
    "fiber": {"unit": "g", "name": "Fiber"},
    "sugar": {"unit": "g", "name": "Sugar"},
    "cholesterol": {"unit": "mg", "name": "Cholesterol"},
    "iron": {"unit": "mg", "name": "Iron"},
    "calcium": {"unit": "mg", "name": "Calcium"},
    "monounsaturated_fat": {"unit": "g", "name": "Monounsaturated Fat"},
    "polyunsaturated_fat": {"unit": "g", "name": "Polyunsaturated Fat"},
    "saturated_fat": {"unit": "g", "name": "Saturated Fat"},
    "potassium": {"unit": "mg", "name": "Potassium"},
    "sodium": {"unit": "mg", "name": "Sodium"},
    "vitamin_a": {"unit": "µg", "name": "Vitamin A"},
    "vitamin_c": {"unit": "mg", "name": "Vitamin C"},
}
FATSECRET_UPDATE_INTERVAL = 15


FATSECRET_FOOD_ENTRIES_ERRORS = {
    2: "Missing required OAuth parameter",
    3: "Unsupported OAuth parameter",
    4: "Invalid signature method",
    5: "Invalid consumer key",
    6: "Invalid/expired timestamp",
    7: "Invalid/used nonce",
    8: "Invalid signature",
    9: "Invalid access token",
}
