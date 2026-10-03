import re
from urllib.parse import urlparse


def extract_urls(text):
    pattern = r'https?://[^\s<>"\']+'
    return re.findall(pattern, text)


def extract_domain(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain