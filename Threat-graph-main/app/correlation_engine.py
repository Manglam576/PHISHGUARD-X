from app.database import db


def find_shared_ip_connections():

    query = """
    MATCH (e1:Email)-[:CONTAINS]->(:URL)-[:BELONGS_TO]->(:Domain)
          -[:RESOLVES_TO]->(ip:IP)<-[:RESOLVES_TO]-(:Domain)
          <-[:BELONGS_TO]-(:URL)<-[:CONTAINS]-(e2:Email)

    WHERE e1.id < e2.id

    MERGE (e1)-[r:CORRELATED_WITH]->(e2)

    SET
        r.reason = "SHARED_IP",
        r.shared_ip = ip.address

    RETURN
        e1.id AS email1,
        e1.subject AS subject1,
        e2.id AS email2,
        e2.subject AS subject2,
        ip.address AS shared_ip
    """

    with db.driver.session() as session:
        results = session.run(query)

        print("\n=== SHARED IP CORRELATIONS ===")

        found = False

        for record in results:
            found = True

            print("\nCorrelation Found!")
            print("Email 1:", record["email1"])
            print("Subject 1:", record["subject1"])
            print("Email 2:", record["email2"])
            print("Subject 2:", record["subject2"])
            print("Shared IP:", record["shared_ip"])

        if not found:
            print("No shared IP correlations found.")


def find_shared_asn_connections():

    query = """
    MATCH (e1:Email)-[:CONTAINS]->(:URL)-[:BELONGS_TO]->(:Domain)
          -[:RESOLVES_TO]->(:IP)-[:BELONGS_TO]->(a:ASN)
          <-[:BELONGS_TO]-(:IP)<-[:RESOLVES_TO]-(:Domain)
          <-[:BELONGS_TO]-(:URL)<-[:CONTAINS]-(e2:Email)

    WHERE e1.id < e2.id

    RETURN
        e1.id AS email1,
        e2.id AS email2,
        a.number AS shared_asn,
        a.organization AS organization
    """

    with db.driver.session() as session:
        results = session.run(query)

        print("\n=== SHARED ASN CORRELATIONS ===")

        found = False

        for record in results:
            found = True

            print("\nASN Correlation Found!")
            print("Email 1:", record["email1"])
            print("Email 2:", record["email2"])
            print("Shared ASN:", record["shared_asn"])
            print("Organization:", record["organization"])

        if not found:
            print("No shared ASN correlations found.")


def run_correlation_engine():

    print("\n================================")
    print("      CORRELATION ENGINE")
    print("================================")

    find_shared_ip_connections()
    find_shared_asn_connections()

    print("\nCorrelation analysis complete!")
