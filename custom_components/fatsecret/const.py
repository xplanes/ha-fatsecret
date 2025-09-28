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
    "calories": "kcal",
    "carbohydrate": "g",
    "protein": "g",
    "fat": "g",
    "fiber": "g",
    "sugar": "g",
    "cholesterol": "mg",
    "iron": "mg",
    "calcium": "mg",
    "monounsaturated_fat": "g",
    "polyunsaturated_fat": "g",
    "saturated_fat": "g",
    "potassium": "mg",
    "sodium": "mg",
    "vitamin_a": "µg",
    "vitamin_c": "mg",
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
