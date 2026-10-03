from app.database import db


def create_threat_graph(
    email_id,
    subject,
    url,
    domain,
    ip,
    asn,
    organization="Unknown"
):

    query = """
    MERGE (e:Email {id: $email_id})
    SET e.subject = $subject

    MERGE (u:URL {value: $url})

    MERGE (d:Domain {name: $domain})

    MERGE (ip_node:IP {address: $ip})

    MERGE (a:ASN {number: $asn})
    SET a.organization = $organization

    MERGE (e)-[:CONTAINS]->(u)
    MERGE (u)-[:BELONGS_TO]->(d)
    MERGE (d)-[:RESOLVES_TO]->(ip_node)
    MERGE (ip_node)-[:BELONGS_TO]->(a)

    RETURN e, u, d, ip_node, a
    """

    parameters = {
        "email_id": email_id,
        "subject": subject,
        "url": url,
        "domain": domain,
        "ip": ip,
        "asn": asn,
        "organization": organization
    }

    with db.driver.session() as session:
        session.run(query, parameters)

    print("Graph updated successfully!")