from app.extractor import extract_urls, extract_domain
from app.enrichment import resolve_domain, get_asn_info
from app.graph_builder import create_threat_graph


def process_email(email_id, subject, email_text):

    print("\nProcessing Email...")
    print("Email ID:", email_id)

    # Step 1: Extract URLs
    urls = extract_urls(email_text)

    if not urls:
        print("No URLs found.")
        return

    print(f"Found {len(urls)} URL(s)")

    # Process every URL
    for url in urls:

        print("\n-------------------")
        print("URL:", url)

        # Step 2: Extract domain
        domain = extract_domain(url)
        print("Domain:", domain)

        # Step 3: Resolve IP
        ip = resolve_domain(domain)

        if not ip:
            print("Could not resolve domain.")
            continue

        print("IP:", ip)

        # Step 4: ASN Lookup
        asn_info = get_asn_info(ip)

        asn = asn_info["asn"]
        organization = asn_info["organization"]

        print("ASN:", asn)
        print("Organization:", organization)

        # Step 5: Create Graph
        create_threat_graph(
            email_id=email_id,
            subject=subject,
            url=url,
            domain=domain,
            ip=ip,
            asn=asn
        )

    print("\nEmail processing complete!")