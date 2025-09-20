# helper function to generate OAuth headers

import aiohttp, time, random, urllib.parse, hmac, hashlib, base64


async def oauth1_request(
    method: str,
    url: str,
    consumer_key: str,
    consumer_secret: str,
    token: str | None = None,
    token_secret: str | None = "",
    params: dict | None = None,
    data: dict | None = None,
    callback_url: str | None = None,
    use_headers: bool = True,
) -> str | dict:
    """
    Make an OAuth1 signed request (GET or POST) to FatSecret API.

    Returns JSON for GET, or text for POST.
    """
    if params is None:
        params = {}
    if data is None:
        data = {}

    # Step 1: create oauth parameters
    oauth_params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": str(random.randint(0, 100000000)),
        "oauth_timestamp": str(int(time.time())),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_version": "1.0",
    }
    if token:
        oauth_params["oauth_token"] = token

    # Add oauth_callback if provided (for request token POST)
    if callback_url:
        oauth_params["oauth_callback"] = callback_url

    # Step 2: merge oauth + query/post parameters for signing
    all_params = {**oauth_params, **params, **data}
    encoded_params = "&".join(
        f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}"
        for k, v in sorted(all_params.items())
    )

    # Step 3: signature
    base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(encoded_params, safe='')}"
    signing_key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret or '', safe='')}"

    # Create signature
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    oauth_params["oauth_signature"] = signature

    # Step 4: build Authorization header
    auth_header = "OAuth " + ", ".join(
        f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in oauth_params.items()
    )

    # Step 5: send request
    async with aiohttp.ClientSession() as session:
        if method.upper() == "GET":
            if use_headers:
                async with session.get(
                    url, headers={"Authorization": auth_header}, params=params
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()

            else:
                async with session.get(url, params=oauth_params, data=data) as resp:
                    resp.raise_for_status()
                    return await resp.text()
        elif method.upper() == "POST":
            if use_headers:
                async with session.post(
                    url, headers={"Authorization": auth_header}, data=data
                ) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            else:
                async with session.post(url, params=oauth_params, data=data) as resp:
                    resp.raise_for_status()
                    return await resp.text()
        else:
            raise ValueError("Only GET or POST supported")
