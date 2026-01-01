import os
import aiohttp

URL_SHORTENER_NAME = "Shlink"
URL_SHORTENER_BASE_API_URL = "https://breia.net"
URL_SHORTENER_VERSION = 3
URL_SHORTENER_API_KEY = os.getenv("URL_SHORTENER_API_KEY")


async def shortenURL(
    url: str,
    custom_slug: str | None = None,
    title: str | None = None,
    valid_since: str | None = None,
    valid_until: str | None = None,
    max_visits: int | None = None,
    tags: list[str] | None = None,
    crawlable: bool = True,
    forward_query: bool = True,
    find_if_exists: bool = True,
    domain: str | None = None,
    short_code_length: int | None = None,
    path_prefix: str | None = None,
):
    headers = {"X-Api-Key": URL_SHORTENER_API_KEY, "Content-Type": "application/json"}

    reqURL = f"{URL_SHORTENER_BASE_API_URL}/rest/v{URL_SHORTENER_VERSION}/short-urls"

    # Construct the body with mandatory longUrl
    body = {
        "longUrl": url,
        "crawlable": crawlable,
        "forwardQuery": forward_query,
        "findIfExists": find_if_exists,
    }

    # Only add optional fields if they are provided
    if custom_slug:
        body["customSlug"] = custom_slug
    if title:
        body["title"] = title
    if valid_since:
        body["validSince"] = valid_since
    if valid_until:
        body["validUntil"] = valid_until
    if max_visits is not None:
        body["maxVisits"] = max_visits
    if tags:
        body["tags"] = tags
    if domain:
        body["domain"] = domain
    if short_code_length:
        body["shortCodeLength"] = short_code_length
    if path_prefix:
        body["pathPrefix"] = path_prefix

    async with aiohttp.ClientSession() as session:
        async with session.post(reqURL, headers=headers, json=body) as response:
            result = await response.json()
            if response.status in [200, 201]:
                return result
            else:
                raise Exception(f"API Error: {result.get('detail', 'Unknown error')}")


async def deleteShortURL(short_code, domain=None):
    # Adjust the version and base URL as per your Shlink setup
    url = f"{URL_SHORTENER_BASE_API_URL}/rest/v{URL_SHORTENER_VERSION}/short-urls/{short_code}"

    # Shlink allows an optional domain query parameter
    params = {}
    if domain:
        params["domain"] = domain

    headers = {"X-Api-Key": URL_SHORTENER_API_KEY, "Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers, params=params) as response:
            if response.status == 204:
                return True

            # If it's not success, grab the error body for the Exception
            error_data = await response.json()
            raise Exception(error_data.get("detail", "Unknown error occurred"))
