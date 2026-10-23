from urllib.parse import urlparse
ALLOWED_SCHEMES = {"http", "https"}

def validate_public_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname:
        raise ValueError("Enter a valid http or https URL.")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or host.endswith(".local"):
        raise ValueError("Local/private URLs are not supported.")
    return url
