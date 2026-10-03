from neo4j import GraphDatabase
import os

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")


class Neo4jConnection:

    def __init__(self):
        self.driver = GraphDatabase.driver(
            URI,
            auth=(USERNAME, PASSWORD)
        )

    def close(self):
        self.driver.close()

    def test_connection(self):
        with self.driver.session() as session:
            result = session.run(
                "RETURN 'Connected to Neo4j!' AS message"
            )
            return result.single()["message"]


db = Neo4jConnection()