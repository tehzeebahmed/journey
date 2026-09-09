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
from llm_router import chat
import json
from file_validations import check_validity_of_files
from cypher_library import QUERY_LIBRARY

CURR_PATH = Path(__file__).parent
# READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("neo4j_cdisc_mock_records.json")
# READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("neo4j_nn_clinical_seed_100.json")
READ_JSOIN_PARAMFILE = CURR_PATH.joinpath("nn_clinical_seed_100_v2.json")
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_KEY"))
neo4j_database = os.getenv("NEO4J_DATABASE")

logging.basicConfig(level=logging.INFO)
GRAPH_SCHEMA = """

Nodes:
Study          {study_id, title, phase}
Visit          {visit_id, name, week}
Subject        {usubjid}
Treatment      {treatment_id, name, type}
DataElement    {element_id, label, cdisc_variable}
Observation    {observation_id, value, unit}
ControlledTerm {code, name, system}

RELATIONSHIPS:
(Study)-[:HAS_VISIT]->(Visit)
(Study)-[:HAS_TREATMENT]->(Treatment)
(Visit)-[:COLLECTS]->(DataElement)
(DataElement)-[:USES_TERM]->(ControlledTerm)
(Subject)-[:RECEIVES]->(Treatment)
(Subject)-[:MADE_OBSERVATION]-(Observation)
(Observation)-[:RECORDED_AT]->(Visit)
(Observation)-[:MEASURED_ELEMENT]->(DataElement)

IMPORTANT:
Observation values are stored as numbers
Visit Weeks: Screenings=-2, Baseline = 0, week 4 = 4 etc
CDISC variables:  BPSYS = Systolic BP, WEIGHT = weight etc
"""

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
    MERGE (o)-[:MEASURED_ELEMENT]-(d)

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


def agent_classify_intent(user_input: str) -> str:
    """
    sends user message to LLM and respond to user query with 
    accoun_brief/payment_history/log_promise/escalate/show_queue/unknown
    """
    PROMPT = f"""
you are an intent classifier for regulatory affairs clinical data copilot.
classify the user's messages into exactly from one of these intents:
- safety_signal : agent wants safety signal from data
- protocol_compliance: agent wants state of compliance
- efficacy_trend: Agent want to see the trends
- data_completeness : agant wants to check on underlying data completeness 
- subject_query: agents want to check the query and get answer
- thought: agents want to compare two treatments 
- unknown: None of the above

reply with only intent label, no other information/text
Intent: """
#  User Message: "{user_input}" 

    messages = [{"role": "system", "content": PROMPT},
                {"role": "user",   "content": user_input}  ]
    intent = chat(messages)
    print(f"User Input: {user_input} \nIntent: {intent}")
    return intent

def agent_genearte_cypher(question: str, intent: str) -> tuple[str, dict]:
    """pick the right query from library and extract parameter(Returns cypher_string and parameters_dict)"""

    # build library description for LLM
    library_desc = "\n".join([f" -{key}: {val['description']} | parameters: {val['parameters']}"
    for key, val in QUERY_LIBRARY.items()])

    # # 1. Access the entire dictionary
    # print(QUERY_LIBRARY)

    # # # 2. Access a specific query's details
    # # query_id = "bp_trend_by_treatment"
    # # query_info = QUERY_LIBRARY[query_id]

    # print(f"Description: {query_info['description']}")
    # print(f"Required Parameters: {query_info['parameters']}")

    prompt = f"""you are a clinical trial data assistant
    choose the appropriate query from this query library and extract parameters

    QUERY LIBRARY:
    {library_desc}

    user QUESTION: {question}
return valid json:
{{
"query_key": "key from the library", "parameters":{{"param_name": value}}, "cannot_answer": False}}
If no query fits set cannot_answer = True and query_key = "".
Notes for parameter extraction:
- treatment_name: "Treatment A" or "Treatment B"
- cdisc_variable: "BPSYS" for blood pressure, "WEIGHT" for weight
- threshold: numeric value (e.g. 140 for BP)
- week: numeric week number (24 for Week 24, 0 for Baseline, -2 for Screening)
- usubjid: subject ID like "SUBJ-00001"
    """

    messages = [
        {"role": "system", "content": "you are clinical trial data parameter extractor. Return only JSON"},
        {"role": "user", "content": prompt}
    ]

    response = chat(messages).strip()

    # Robust Markdown and Wrapper Cleaner
    if "{" in response and "}" in response:
        # Extract everything from the first '{' to the last '}'
        response = response[response.find("{"):response.rfind("}") + 1]
    
    # if markdown is addewd - lets clean it
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    try:
      result = json.loads(response.strip())
    except Exception as e:
        print(f"Failed to parse LLM Response: {response}")
        raise e
    
    if result.get("cannot_answer"):
        return None, {}

    query_key = result.get("query_key")
    parameters = result.get("parameters", {})
        # Ensure the key exists in your library before accessing
    if query_key not in QUERY_LIBRARY:
        return None, {}
    cypher = QUERY_LIBRARY[query_key]["cypher"]
    return cypher, parameters

def agent_generate_narrative(question: str, cypher: str, raw_result: list) -> str:
    """this agent generate acutal result into common lamguage Regulatory narrative"""
    prompt = f"""
You are a clinical data scientist preparing a summary for regulatory affiard director(avove D level)

Original Question: {question}
Query executed: {cypher}
Raw Results: {json.dumps(raw_result, indent = 2)}

write a formal clinical narrative answering the question.
Requirement: 
 - use Clinical terminology
 - Cite specific Subject when relevant
 - Highlight safety signals or anomalies
 - Conclude with Regulatory implicatrions if any
 - write complete narrative before going to any other task in Maximum 200 words
"""
    messages = [
        {"role": "system", "content": "you are a regulatory affairs clinical data  expert"},
        {"role": "user", "content": prompt}
    ]

    return chat(messages)

def run_clinical_copilot(driver, db_name):
    """Final copilot to run entire machinery on clinical trial regulatory affairs"""
    conversation_history = []
    while True:
        print("\n************")
        question = input("Director : ").strip()
        print("************\n")
        if question.lower() == "exit":
            break

        # step 1 - Intent classifier
        intent = agent_classify_intent(question)
        print(f"\nThe intent of Director is : {intent}")

        # Step 2 Cyphey Genearte
        cypher, parameters  = agent_genearte_cypher(question, intent)
        if cypher is None:
          print(f"\nThe question cannot be answered from current study data.\n")
          continue

        print(f"[Query: {[k for k, v in QUERY_LIBRARY.items() if v["cypher"]==cypher][0]}]")

        # step 3 - generate result from neo4j/Auradb
        try:
          results, _, _ = driver.execute_query(cypher, parameters, database_= db_name)
          raw_result = [dict(r) for r in results]
        except Exception as e:
            print(f"error raised at execution - {e}\n")
            continue

        # step 4 - Narration generation
        narrative = agent_generate_narrative(question, cypher, raw_result)
        clean_narrative = narrative

        # step 5 conversation history 
        conversation_history.append(
            {"Question": {question}, "Intent": {intent}, "Narrative": {narrative}}
        )

        print(f"\n Copilot : {clean_narrative}", flush=True)

        
def main():
    tee_stream = start_tee(__file__)
    check_validity_of_files(READ_JSOIN_PARAMFILE)
    print("Executing seeding of data.....")
    driver = get_neo4j_driver()

    # driver.execute_query("MATCH (n) DETACH DELETE n", database_= neo4j_database)

    # agent_seed_clinical_data(driver, neo4j_database)
    run_clinical_copilot(driver, neo4j_database)
    # print("Priting of data.....")
    # agent_verify_and_read_graph(driver, neo4j_database)

    stop_tee(tee_stream)

if __name__ == "__main__":
    main()

"""

Study
  ├── HAS_VISIT → Visit
  │                 └── COLLECTS → DataElement
  │                                    └── USES_TERM → ControlledTerm (SNOMED-CT)
  ├── HAS_TREATMENT → Treatment
  │                      ↑ RECEIVES
  │                   Subject
  │                      └── MADE_OBSERVATION → Observation
  │                                               ├── RECORDED_AT → Visit
  │                                               └── MEASURED_ELEMENT → DataElement

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

MATCH
  (s:Subject)-[:MADE_OBSERVATION]->(o:Observation)-[:RECORDED_AT]->(v:Visit),
  (o)-[:KEASURED_ELEMENT]->(d:DataElement)
RETURN
  s.usubjid AS Subject,
  v.name AS Visit,
  d.label AS DataElement,
  o.value AS Value,
  o.unit AS Unit
ORDER BY Subject, v.week


Component 1 — Intent Classifier
  What is the director asking about?
  safety_signal / protocol_compliance / 
  efficacy_trend / data_completeness / subject_query

Component 2 — Cypher Generator
  Converts question + intent into valid Cypher query
  Uses graph schema as context

Component 3 — Neo4j Executor  
  Runs the Cypher, returns raw results

Component 4 — Clinical Narrator
  Converts raw graph results into regulatory narrative
  Formal tone, clinical terminology, action-oriented

Component 5 — Conversation Memory
  Director can ask follow-up questions
  "And for Treatment B?" → remembers context
  
  """