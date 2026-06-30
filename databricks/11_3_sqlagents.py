from urllib import response
import urllib.parse
import snowflake.connector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_snowflake_data():
    """Fetch data from Snowflake using Gemini agent with SQL toolkit."""
    
    logger.info("Fetching data from Snowflake using Gemini agent...") 
    # Configuration
    SNOWFLAKE_USER = "tehzeebahmed"
    SNOWFLAKE_ACCOUNT = "qlszxwi-ri93338"
    SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
    SNOWFLAKE_DATABASE = "LOCALT"
    SNOWFLAKE_SCHEMA = "PUBLIC"
        
    # Get password from user
    password = input("Enter your Snowflake password: ")
    encoded_password = urllib.parse.quote_plus(password)
        
    # Step 1: Test connection with snowflake.connector
    logger.info("Establishing connection to Snowflake...")
    ctx = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=password,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
    #ctx.close()
    logger.info("Snowflake connection successful.")
        
    # Step 3: Create SQLDatabase object
    logger.info("Creating SQLDatabase connection...")
       
    # Step 4: Query using the agent
    snowflake_query = "Select * from universities where university_id = 1"
    logger.info(f"Executing query: {snowflake_query}")

    try:
        # 2. Open cursor and execute inside the try block
        cur = ctx.cursor()
        cur.execute(snowflake_query)
        #get this data from the cursor and print it 
        # in JSON format using the column names as keys and the values as values
        rows = cur.fetchall()
        results = [dict(zip([key[0] for key in cur.description], row)) for row in rows]
        cur.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()
    
    
    logger.info("Data fetched successfully from Snowflake.")
    print("\n--- Query Result ---")
    for row in results:
        print(row)

    
def fetch_databricks_data():
    # Use the gemini_agent to fetch data from Databricks
    logger.info("Fetching data from Databricks using Gemini agent...")
    databricks_query = "SELECT * FROM locations where location_id = {results[0]['location_id']};"
    dcurr.execute(databricks_query)
    databricks_data = dcurr.fetchall()
    
    if databricks_data:
        logger.info("Data fetched successfully from Databricks.")
    else:        
        logger.error("Failed to fetch data from Databricks.")
    return databricks_data


def fetch_local_csv_data():
    # Use the gemini_agent to fetch data from the local CSV file
    logger.info("Fetching data from local CSV file using Gemini agent...")
    csv_data = gemini_agent.invoke("Read the contents of the local CSV file.").text.strip()
    if csv_data:
        logger.info("Data fetched successfully from local CSV file.")
    else:
        logger.error("Failed to fetch data from local CSV file.")
    return csv_data

def main():
    #databricks_data = fetch_databricks_data()
    snowflake_data = fetch_snowflake_data()
    # Process the data and create a CSV file with the combined data from both sources
    # This part will involve parsing the data, merging it based on location_id, and writing it to a CSV file    
    # You can use pandas or the csv module to create the CSV file
    # For example, using pandas:
    
    # Assuming databricks_data and snowflake_data are in a format that can be converted to DataFrames
    databricks_df = pd.DataFrame([x.split(',') for x in databricks_data.split('\n')], columns=['location_id', 'location_name', 'city', 'state', 'country', 'latitude', 'longitude'])
    snowflake_df = pd.DataFrame([x.split(',') for x in snowflake_data.split('\n')], columns=['university_id', 'university_name', 'country', 'location_id'])
    # Merge the DataFrames on location_id
    #merged_df = pd.merge(databricks_df, snowflake_df, on='location_id')
    # Write the merged DataFrame to a CSV file
    #merged_df.to_csv('combined_data.csv', index=False)
    logger.info("Combined data saved successfully to 'combined_data.csv'.")

    #lets write this data from snowflake to a csv file
    snowflake_df.to_csv('snowflake_data.csv', index=False)
    logger.info("Snowflake data saved successfully to 'snowflake_data.csv'.")


if __name__ == "__main__":
    fetch_snowflake_data()
    