"""
In this exercise we will be connecting to 
1. Databricks SQL Endpoint
2. Snowflake SQL Warehouse and reading from both of them using Python.
and then a csv file will be created with the data read from the Databricks SQL Endpoint and Snowflake SQL Warehouse.

databricks database has locations table with this schema -
location_id number,
location_name string,
city string,
state string,
country string,
latitude double,
longitude double

also users table with the schema
users
user_id number,
user_name string,
email string,
phone string,
location_id number

snowflake database has universities table with this schema -
university_id number, 
university_name string, 
country string,
location_id number.

now I will take user , university and location data from these two databases and create a csv file with the following schema -
user_id, user_name, email, phone, university_name, country, location_name, city, state, country, latitude, longitude

"""
from urllib import response
import urllib.parse
import snowflake.connector
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
