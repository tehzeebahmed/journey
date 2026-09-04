"""
this Script creates nodes, relationships and add elements to a study graph for novo
"""

import os
from pathlib import Path
import config
from tee_logger import start_tee, stop_tee
from neo4j import GraphDatabase
import logging
import json
from file_validations import check_validity_of_files

CURR_PATH = Path(__file__).parent
# READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("neo4j_cdisc_mock_records.json")
READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("neo4j_nn_clinical_seed_100.json")
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_KEY"))
neo4j_database = os.getenv("NEO4J_DATABASE")

logging.basicConfig(level=logging.INFO)

def get_neo4j_driver():
    """gets driver and checks connection to neo4j graph database"""
    graph_driver =  GraphDatabase.driver(uri= URI, auth = AUTH)
    try:
        graph_driver.verify_connectivity()
        print(f"Connectiosn are doing fine for {URI}")
        return graph_driver
    except Exception as e:
        print(f"\nThe Error is {e}")
        graph_driver.close()
        return None

def agent_seed_clinical_data(driver, db_name):
    """Ingests mock data following the Study->Visit->DataElement->ControlledTerm chain."""

    # Query Parameters mimicking standard Clinical Data Interchange Standards (CDISC)
    with open (READ_JSOIN_PARAMFILE, "r") as file_read:
        records = json.load(file_read)
    logging.info(f"JSON file with records - {len(records)} loaded succesfully")
    

    # Executing transactional block using MERGE to avoid duplicate insertions
    cypher_ingest = """

    // 1. Create Study node
    MERGE (s:Study {study_id: $study_params.id})
    ON CREATE SET 
                s.title = $study_params.title, 
                s.phase = $study_params.phase
    
    // 2. Create Visit node and link via HAS_VISIT
    MERGE (v:Visit {visit_id: $visit_params.id})
    ON CREATE SET 
                v.name = $visit_params.name, 
                v.week = $visit_params.week
    MERGE (s)-[:HAS_VISIT]->(v)
    
    // 3. Create DataElement node and link via COLLECTS
    MERGE (d:DataElement {element_id: $element_params.id})
    ON CREATE SET 
                d.label = $element_params.label, 
                d.cdisc_variable = $element_params.variable
    MERGE (v)-[:COLLECTS]->(d)
    
    // 4. Create ControlledTerm node (SNOMED / CDISC standard) and link via USES_TERM
    MERGE (c:ControlledTerm {code: $term_params.code})
    ON CREATE SET 
                c.name = $term_params.name, 
                c.system = $term_params.system
    MERGE (d)-[:USES_TERM]->(c)
    
    MERGE (sub:Subject {
        usubjid: $subject.usubjid
    })

    MERGE (sub)-[obs:HAS_OBSERVATION]->(d)
    SET obs.value = $subject.value,
        obs.unit = $subject.unit,
        obs.visit_id = $visit_params.id
    
    // 6. FIXED MAPPING: Unwind the treatments list to process each treatment individually
    WITH s, v, d, sub, obs, $treatment_params AS treatments_list
    UNWIND treatments_list AS trt
    
    MERGE (t:Treatment {treatment_id: trt.id})
    ON CREATE SET
                t.name = trt.name,
                t.type = trt.type

    MERGE (s)-[:HAS_TREATMENT]->(t)
    MERGE (sub)-[:RECEIVES]->(t)
    
    RETURN
        s.study_id AS study,
        t.name AS treatment,
        v.name AS visit,
        d.cdisc_variable AS variable,
        sub.usubjid AS subject,
        obs.value AS value,
        obs.unit AS unit
    """
    
    for record in records:
        params = {
            "study_params": record["study_params"],
            "visit_params": record["visit_params"],
            "element_params": record["element_params"],
            "term_params": record["term_params"],
            "treatment_params": record["treatments"],
            "subject": record["subject_data"]
        }

        result = driver.execute_query(cypher_ingest, params, database_= db_name)
        records_created = result[0]
        for row in records_created:
            logging.info(f"Successfully linked: {record['study_params']} ➔ {record['visit_params']} ➔ {record['element_params']} ➔ {record['term_params']}")

def agent_verify_and_read_graph(driver: str, db_name: str):
    """Queries the graph path back out to print the mapped metadata chain."""

    cypher_query = """
    MATCH path = (s:Study)-[:HAS_VISIT]->(v:Visit)-[:COLLECTS]->(d:DataElement)-[:USES_TERM]->(c:ControlledTerm)
    RETURN s.study_id AS study, v.name AS visit, d.label AS element, c.name AS terminology, c.system AS standard
    """
    records, _, _ = driver.execute_query(cypher_query, database_=db_name)
    
    print("\n--- MAPPED CLINICAL METADATA PATHWAY ---")
    for record in records:
        print(f"Study:        [{record['study']}]")
        print(f"  └── Visit:  {record['visit']}")
        print(f"       └── Collects: {record['element']}")
        print(f"            └── Standard Term: {record['terminology']} ({record['standard']})")

def main():
    tee_stream = start_tee(__file__)
    check_validity_of_files(READ_JSOIN_PARAMFILE)
    print("Executing seeding of data.....")
    driver = get_neo4j_driver()

    driver.execute_query("MATCH (n) DETACH DELETE n", database_= neo4j_database)

    agent_seed_clinical_data(driver, neo4j_database)
    print("Pronting of data.....")
    agent_verify_and_read_graph(driver, neo4j_database)

    stop_tee(tee_stream)

if __name__ == "__main__":
    main()
