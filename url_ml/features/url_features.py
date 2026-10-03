from urllib.parse import urlparse, parse_qs
import ipaddress
import re
import tldextract


# URL shortener domains
SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "buff.ly",
    "cutt.ly",
    "rb.gy",
    "shorturl.at",
}


# TLDs we will initially mark as suspicious.
# This is only a feature, NOT a final verdict.
SUSPICIOUS_TLDS = {
    "xyz",
    "top",
    "click",
    "zip",
    "work",
    "country",
    "gq",
    "tk",
    "ml",
    "ga",
    "cf",
}


def is_ip_address(host: str) -> int:
    """
    Return 1 if the hostname is an IPv4/IPv6 address, otherwise 0.
    """
    if not host:
        return 0

    try:
        ipaddress.ip_address(host)
        return 1
    except ValueError:
        return 0


def count_special_characters(url: str) -> int:
    """
    Count characters other than letters, digits and common URL separators.
    """
    return sum(
        1 for char in url
        if not char.isalnum() and char not in ".:/?&=#_-"
    )


def extract_url_features(url: str) -> dict:
    """
    Convert a URL into numerical features used by the XGBoost model.
    """

    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")

    url = url.strip()

    # urlparse works best when a scheme is present.
    parsed = urlparse(url)

    # If someone passes example.com instead of https://example.com
    if not parsed.netloc:
        parsed = urlparse("http://" + url)

    host = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""
    fragment = parsed.fragment or ""

    # tldextract separates:
    # subdomain + domain + suffix
    extracted = tldextract.extract(url)

    subdomain = extracted.subdomain
    domain = extracted.domain
    suffix = extracted.suffix

    query_params = parse_qs(query)

    features = {
        # Basic URL structure
        "url_length": len(url),
        "domain_length": len(host),
        "path_length": len(path),

        # Structural features
        "dot_count": url.count("."),
        "subdomain_count": (
            len(subdomain.split("."))
            if subdomain
            else 0
        ),

        # Character features
        "digit_count": sum(char.isdigit() for char in url),
        "letter_count": sum(char.isalpha() for char in url),
        "hyphen_count": url.count("-"),
        "at_count": url.count("@"),
        "special_char_count": count_special_characters(url),

        # Query / fragment
        "query_param_count": len(query_params),
        "fragment_count": 1 if fragment else 0,

        # Security-related URL properties
        "has_ip": is_ip_address(host),
        "has_punycode": int("xn--" in host.lower()),
        "has_https": int(parsed.scheme.lower() == "https"),

        # Domain indicators
        "is_shortened": int(host.lower() in SHORTENER_DOMAINS),
        "suspicious_tld": int(
            suffix.lower() in SUSPICIOUS_TLDS
        ),
    }

    return features


if __name__ == "__main__":
    test_url = "https://secure-login.example.com/account?id=123"

    features = extract_url_features(test_url)

    print("URL:")
    print(test_url)

    print("\nExtracted features:")
    for name, value in features.items():
        print(f"{name}: {value}")