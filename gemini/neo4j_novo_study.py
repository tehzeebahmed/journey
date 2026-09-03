from neo4j import GraphDatabase
import config
import os

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_KEY"))
print(URI)
neo4j_database = os.getenv("NEO4J_DATABASE")

# 2. Establish and verify the connection
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    try:
        driver.verify_connectivity()
        print("Successfully connected to the Neo4j instance!")
        
        # Example: Running a simple Cypher query
        records, summary, keys = driver.execute_query(
            "MATCH (n) RETURN count(n) AS total_nodes",
            database_ = neo4j_database # Explicitly specify your database if needed
        )
        print(neo4j_database)
        for record in records:
            print(f"Total nodes in database: {record['total_nodes']}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

