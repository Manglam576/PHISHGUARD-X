import socket
import urllib.request
import json


def resolve_domain(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        return None


def get_asn_info(ip):
    """
    Looks up ASN information for an IP address.
    Returns ASN and organization if available.
    """

    try:
        url = f"https://ipinfo.io/{ip}/json"

        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())

        org = data.get("org", "Unknown")

        # Example org format: "AS15169 Google LLC"
        parts = org.split(" ", 1)

        asn = parts[0] if parts and parts[0].startswith("AS") else "Unknown"
        organization = parts[1] if len(parts) > 1 else org

        return {
            "asn": asn,
            "organization": organization
        }

    except Exception as e:
        print(f"ASN lookup failed: {e}")

        return {
            "asn": "Unknown",
            "organization": "Unknown"
        }