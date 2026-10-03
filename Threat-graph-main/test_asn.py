from app.enrichment import resolve_domain, get_asn_info


domain = "google.com"

ip = resolve_domain(domain)

print("Domain:", domain)
print("IP:", ip)

if ip:
    asn_info = get_asn_info(ip)

    print("ASN:", asn_info["asn"])
    print("Organization:", asn_info["organization"])