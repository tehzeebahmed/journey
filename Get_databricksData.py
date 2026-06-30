# in this python script we will connect to databricks with connector
# do a select for a row in the locations table and print the result in JSON format
# and then we will print it in a nice format using the column names as keys and the values as values
import databricks.sql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)    

def fetch_databricks_data():
    """Fetch data from Databricks using connector agent with SQL toolkit."""
    
    logger.info("Fetching data from Databricks using connector agent...") 
    # Configuration
    DATABRICKS_SERVER_HOSTNAME = "dbc-qlszxwi-ri93338.cloud.databricks.com"
    DATABRICKS_HTTP_PATH = "sql/protocolv1/o/0/1234567890123456/0123-456789-abcdefg"
    DATABRICKS_ACCESS_TOKEN = "dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX-3"
    
    # Step 1: Test connection with databricks.sql
    logger.info("Establishing connection to Databricks...")
    conn = databricks.sql.connect(
        server_hostname=DATABRICKS_SERVER_HOSTNAME,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_ACCESS_TOKEN
    )
    logger.info("Databricks connection successful.")
    
    # Step 2: Query using the agent
    databricks_query = "SELECT * FROM locations WHERE location_id = 1"
    logger.info(f"Executing query: {databricks_query}")
    
    try:
        cur = conn.cursor()
        cur.execute(databricks_query)
        databricks_data = cur.fetchall()
        # Print the result in JSON format using the column names as keys and the values as values
        databricks_results = [dict(zip([key[0] for key in cur.description], row)) for row in databricks_data]
        print(databricks_results)
        cur.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()

