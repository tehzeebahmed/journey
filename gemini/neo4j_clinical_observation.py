"""
this Script creates nodes, relationships and add elements to a clinical observation study
 graph for novo
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
# READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("neo4j_nn_clinical_seed_100.json")
READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("nn_clinical_seed_100_v2.json")
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
    
    //observation Node addition 
    MERGE (o:Observation {observation_id: $observation_params.id})
    ON CREATE SET 
                o.value = $observation_params.value, 
                o.unit = $observation_params.unit

    //Draw the clinks (connection links) to link everything into the new node anchore
    MERGE (sub)-[:MADE_OBSERVATION]->(o)
    MERGE (o)-[:RECORDED_AT]->(v)
    MERGE (o)-[:KEASURED_ELEMENT]-(d)

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
            "treatment_params": record["treatment_params"],
            "subject": record["subject_data"],
            "observation_params": record["observation_params"]
        }

        result = driver.execute_query(cypher_ingest, params, database_= db_name)
        records_created = result[0]
        for row in records_created:
            logging.info(f"Successfully linked: {record['study_params']} ➔ {record['visit_params']} ➔ {record['element_params']} ➔ {record['term_params']} -> {record['observation_params']}")

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

"""

Study
 ├── HAS_VISIT ──> Visit
 │                    │
 │                 COLLECTS
 │                    ↓
 │               DataElement
 │                    │
 │                USES_TERM
 │                    ↓
 │              ControlledTerm
 │
 └── HAS_TREATMENT ──> Treatment
                          ↑
                       RECEIVES
                          │
                       Subject
                          │
                   HAS_OBSERVATION
                          ↓
                     Observation
                       /       \
                  AT_VISIT   FOR_ELEMENT
                     ↓           ↓
                   Visit     DataElement


MATCH (n)
RETURN labels(n)[0] AS NodeLabel, count(n) AS TotalNodes
ORDER BY TotalNodes DESC

This audit query generates a matrix showing exactly which variables are being collected at which specific visits to check protocol compliance.
MATCH (s:Study)-[:HAS_VISIT]->(v:Visit)-[:COLLECTS]->(de:DataElement)
RETURN
  s.study_id AS Study,
  v.name AS VisitName,
  v.week AS VisitWeek,
  de.cdisc_variable AS Variable,
  de.label AS VariableLabel
ORDER BY Study, VisitWeek, Variable

A vital quality control query for graph databases. This checks if any Observation nodes exist without a valid link to a Subject, Visit, or DataElement. (It should return 0 rows).
MATCH (o:Observation)
WHERE
  NOT EXISTS { (:Subject)-[:MADE_OBSERVATION]->(o) } OR
  NOT EXISTS { (o)-[:RECORDED_AT]->(:Visit) } OR
  NOT EXISTS {
  (o)-[:KEASURED_ELEMENT]->(:DataElement)
  }
RETURN o

List All Observations for a Specific Subject
MATCH (sub:Subject {usubjid: 'SUBJ-00001'})-[:MADE_OBSERVATION]->(o:Observation)
MATCH (o)-[:RECORDED_AT]->(v:Visit)
MATCH (o)-[:MEASURED_ELEMENT]->(d:DataElement)
RETURN v.name AS Visit, d.cdisc_variable AS Variable, o.value AS Value, o.unit AS Unit
ORDER BY v.week ASC

Find out how many total observations (like blood pressure or weight readings) have been logged across different treatment arms.
MATCH
  (t:Treatment)<-[:RECEIVES]-(sub:Subject)-[:MADE_OBSERVATION]->(o:Observation)
RETURN t.name AS TreatmentName, count(o) AS TotalObservations

Isolate a specific data element (like WEIGHT) and track how the values change chronologically from Screening to Week 24 for all patients.
MATCH
  (s:Subject)-[:MADE_OBSERVATION]->
  (o:Observation)-[:KEASURED_ELEMENT]->
  (de:DataElement)
MATCH (o)-[:RECORDED_AT]->(v:Visit)
WHERE
  de.cdisc_variable = 'WEIGHT' AND
  (v.name = 'Screening' OR (v.week >= 0 AND v.week <= 24))
RETURN
  s.usubjid AS patient,
  v.name AS visit,
  v.week AS week,
  o.value AS value,
  o.unit AS unit
ORDER BY s.usubjid, v.week

Ensure your observations map perfectly back to standard medical coding dictionaries (like SNOMED-CT).
MATCH
  (o:Observation)-[:KEASURED_ELEMENT]->
  (de:DataElement)-[:USES_TERM]->
  (ct:ControlledTerm)
WHERE ct.system = 'SNOMED-CT'
RETURN
  o.observation_id AS observation_id,
  o.value AS value,
  de.label AS element_label,
  ct.name AS term_name,
  ct.code AS term_code,
  ct.system AS dictionary

  Find patients showing elevated measurements. Since values are stored as numbers or strings depending on your exact payload, this query safely converts them dynamically using toFloat() to filter.
  MATCH
  (s:Subject)-[:MADE_OBSERVATION]->
  (o:Observation)-[:KEASURED_ELEMENT]->
  (de:DataElement)
WHERE toFloat(o.value) > 100.0
RETURN
  s.usubjid AS PatientID,
  de.cdisc_variable AS Test,
  o.value AS Value,
  o.unit AS Unit

See the starting baseline values across arms. This query groups subjects by their treatment, isolates the Baseline visit, and calculates the statistical mathematical average.
MATCH
  (t:Treatment)<-[:RECEIVES]-
  (s:Subject)-[:MADE_OBSERVATION]->
  (o:Observation)-[:RECORDED_AT]->
  (v:Visit)
WHERE v.name = 'Baseline'
MATCH (o)-[:KEASURED_ELEMENT]->(de:DataElement)
RETURN
  t.name AS Treatment,
  de.cdisc_variable AS Variable,
  avg(o.value) AS AverageValue

 Which subjects with Treatment A had systolic BP > 130 at Week 4?
 MATCH (s:Subject)-[:RECEIVES]->(t:Treatment)
WHERE t.name = 'Treatment A'
MATCH (s)-[:MADE_OBSERVATION]->(o:Observation)-[:RECORDED_AT]->(v:Visit)
WHERE v.week = 4 AND o.value > 130
MATCH (o)-[:KEASURED_ELEMENT]->(de:DataElement)
WHERE toLower(de.label) CONTAINS 'systolic' OR de.cdisc_variable = 'SYSBP'
RETURN DISTINCT s.usubjid

let’s verify the new Observation model
MATCH (s:Subject)-[:HAS_OBSERVATION]->(o:Observation)
RETURN s.usubjid AS Subject,
       o.observation_id AS Observation,
       o.value AS Value,
       o.unit AS Unit
LIMIT 10;

"""