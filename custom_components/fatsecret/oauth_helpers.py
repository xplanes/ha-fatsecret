# helper function to generate OAuth headers

import urllib.parse
import hmac
import hashlib
import base64


def oauth_build_base_string(method, url, params):
    """Construct the OAuth base string."""
    sorted_params = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(params.items())
    )
    return "&".join(
        [
            method.upper(),
            urllib.parse.quote(url, safe=""),
            urllib.parse.quote(sorted_params, safe=""),
        ]
    )


def oauth_generate_signature(
    base_string: str, consumer_secret: str, token_secret: str
) -> str:
    """Generate the OAuth signature."""
    key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    hashed = hmac.new(key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(hashed.digest()).decode("utf-8")


def oauth_build_authorization_header(oauth_params):
    """Build the OAuth Authorization header."""
    auth_header = "OAuth " + ", ".join(
        f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in oauth_params.items()
    )
    return auth_header
