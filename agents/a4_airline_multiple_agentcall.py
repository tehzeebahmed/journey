'''
main()
  ↓
extract_cities(user_query)  ← new function, calls LLM
  ↓
for city in cities:
    get_ticket_price(city)  ← existing tool, called in loop
  ↓
ask_agent(cities, results)  ← existing function, updated to handle multiple
'''
import os
import sqlite3
import config
import json
from tee_logger import stop_tee, start_tee
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

db = "ticketing.db"
SYSTEM_PROMPT = "You are an helpful airline assistant, you provide details on tickets from origin" \
"and to destination city or only to destination and you only give results back from what yoy get from tools, if that route is not available you propose another route and its cost"

client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))
#client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url=os.getenv("GROQ_BASE_URL"))
if client:
    print("api key issue sorted")
else:
    print("groq has some problem")
# *********************************************************************
# Define the three tools that LLM can call with the strict JSON Schema
# Strict Schemas prevetns unexpected inputs (secutrity best practices)
# *********************************************************************

#Tool 1 - get flight prices
GET_FLIGHT_PRICES = {
    "type": "function",
    "function":{
        "name": "get_flight_prices",
        "description": "To get the flight prices between Origin and Destination",
        "parameters": {
            "type": "object",
            "properties":{
                "origin": {
                    "type": "string",
                    "description": "name of the origin city"
                },
                "destination":{
                    "type": "string",
                    "description": "Name of the destination city"
                }
            },
            "required": ["origin", "destination"],
            "additionalProperties": False
        }
    }
}

#tool 2 - get flight to destination
GET_FLIGHT_TO = {
    "type": "function",
    "function": {
        "name": "get_flights_to",
        "description": "Get all available flights to a destination from any origin city",
        "parameters":{
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Name of the destination city"
                }
            },
            "required": ["destination"],
            "additionalProperties": False
        }
    }
}
# combine all tools into a Single List for easy passing to LLM
AVAILABLE_TOOLS = [GET_FLIGHT_PRICES, GET_FLIGHT_TO]

def insert_data_intodb():
    """Create table and insert seed data if not already present."""
    flights = [
        ("Delhi", "London", 1677, 9.5, "Air India", 5),
         ("Delhi", "London", 1277, 9.5, "Air India", 4),
         ("Delhi", "London", 1807, 7.3, "Pasha Air", 5),
         ("Delhi", "Paris", 1407, 6.4, "Pasha Air", 5),
         ("Mumbai", "Paris", 1287, 6.4, "Air India", 5),
         ("Hyderabad", "Paris", 1287, 9.4, "Air India", 4),
         ("Delhi", "Tokyo", 1029, 11.23, "Indigo", 5),
         ("Delhi", "Tokyo", 729, 11.23, "Air India", 3),
         ("Delhi", "Tokyo", 829, 11.23, "Indigo", 4),
         ("Delhi", "Seol", 1229, 10.23, "Air India", 5),
         ("Mumbai", "London", 980, 8.49, "British Airways", 4),
         ("Mumbai", "London", 9185, 8.49, "United Airlines", 5),
         ("Pune", "New York", 1100, 13.23, "Cathey Pacific", 5),
         ("Pune", "New York", 990, 13.23, "Air India", 4),
         ("Mumbai", "New York", 1322, 11.34, "Cathey Pacific", 5),
         ("Mumbai", "New York", 1121, 12.30, "Cathey Pacific", 4),
         ("Mumbai", "New York", 1282, 11.34, "Indigo", 5),
         ("Moradabad", "Delhi", 289, 1.2, "Indigo", 3),
         ("Pune", "London", 766, 7.46, "British Airways", 4),
         ("Hyderabad", "New York", 1101, 12.7, "United Airlines", 5)    
    ]

    try:
        with sqlite3 .connect(db) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS flights (Id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin text NOT NULL, 
            destination text NOT NULL, 
            price INTEGER NOT NULL, 
            destinationHrs real NOT NULL, 
            airline TEXT NOT NULL,
            star INTEGER NOT NULL,
            UNIQUE(origin, destination, airline, price))""")
            
            conn.executemany( """INSERT OR IGNORE INTO flights (origin, destination, price, destinationHrs, airline, star) values(?, ?, ?, ?, ?, ?)""", flights)
            conn.commit()
        #print(f"[db] Database ready: {db}")
    except sqlite3.Error as e:
        print(f"[db] Error initializing database: {e}")
def get_flight_prices(origin: str, destination: str):
    """Fetch all flights for a given origin → destination route."""
    try:
        with sqlite3.connect(db) as conn:
            cursor = conn.execute("""
                SELECT airline, price, destinationHrs, star
                FROM flights
                WHERE origin      = ? COLLATE NOCASE
                AND   destination = ? COLLATE NOCASE
                ORDER BY price ASC""", 
                (origin, destination))
            results = cursor.fetchall()

            if results:
                print(f"\n Flights from {origin} to {destination } :")
                print(f" {'Airline':<20} {'Price':>8} {'Duration':>10} {'Stars':>6}")
                print('-' * 60)
                for airline, price, hrs, stars in results:
                    print(f" {airline:<20} ${price:>7} {hrs:>9.1f}h {'★' * stars}")
                    print('-' * 60)
            else:
                print(f"\n No direct flight benween {origin} to {destination}")
                # suggest alternatives — find other origins that fly to destination
                with sqlite3.connect(db) as conn:
                    cursor = conn.execute(""" SELECT DISTINCT origin, destination, airline, min(price) as min_price, star from flights where destination = ? COLLATE NOCASE
                                            GROUP BY origin, destination, airline, star order by min_price""", (destination,))
                    alternative_flights = cursor.fetchall()
                    if alternative_flights:
                        print("\n Available flights are :")
                        print(f"{'Origin':<13} {'Destination':<13} {'Airline':<20} {'Price':>8}  {'Stars':>6}")
                        print('-' * 60)
                        for origin, destination, airline, min_price, star in alternative_flights:
                            print(f"{origin:<13} {destination:<13} {airline:<20} {min_price:>8}  {'★' * star}")
                            print('-' * 60)
    except sqlite3.Error as e:
            print(f"[db] Server is down - cant check :) {e}")
    
def get_flights_to(destination: str):
    """ to get flights if I just sepecify what is my destination city"""
    try:
        with sqlite3.connect(db) as conn:
            cursor = conn.execute(""" 
                SELECT origin, airline, price, destinationHrs, star
                FROM flights
                WHERE destination = ? COLLATE NOCASE
                ORDER BY price ASC""", (destination,))
            
            results = cursor.fetchall()
            if results:
                print(f"\n Flights for {destination } :")
                print(f"{'origin':<13} {'Airline':<20} {'Price':>8} {'Duration':>10} {'Stars':>6}")
                print('-' * 60)
                for origin, airline, price, destinationHrs, star in results:
                    print(f"{origin:<13} {airline:<20} ${price:>7} {destinationHrs:>9.1f}h {'★' * star}")
                    print('-' * 60)
    except sqlite3.Error as e:
        print(f"[db] Server is down - cant check :) {e}")

# ── Tool dispatcher ────────────────────────────────────────────────────────────
def call_tool(tool_name: str, tool_args: dict) -> str:
    """Calls the right function based on what LLM requested."""
    print(f" LLM calls the tool : {tool_name} and the tool args: {tool_args}")
    if tool_name == "get_flight_prices":
        return (get_flight_prices(**tool_args))
    elif tool_name == "get_flights_to":
        return(get_flights_to(**tool_args))
    else:
        return (f"unknow tool {tool_name}")


def run_agent(user_query: str) -> str:
    """
    Full agent loop:                              
    1. Send query to LLM with tools
    2. LLM decides which tool to call
    3. We run the tool and get DB results
    4. Send results back to LLM
    5. LLM gives final natural language answer
    """
    print('-'*60)
    print(f"user query : {user_query}")
    print('-' * 60)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    # Step 1 — first LLM call: decides which tool to use
    response = client.chat.completions.create(model=os.getenv("GEMINI_MODEL_NAME"),
                                              messages=messages,
                                              tools=AVAILABLE_TOOLS,
                                              tool_choice="auto")
    
    reply = response.choices[0].message
    # Step 2 — check if LLM wants to call a tool
    if reply.tool_calls:
        # add LLM's tool call decision to message history
        messages.append(reply)

        # Step 3 — execute each tool the LLM requested
        for tool_call in reply.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            tool_result = call_tool(tool_name, tool_args)
            print(f"\n [tool Result] - {tool_result}")

            # Step 4 — add tool result to messages so LLM can read it
            messages.append({
                "role": "tool", "tool_call_id": tool_call.id,
                "content": tool_result
            })

            #Step 5 - LLM gives friendly results  using tools and its results
            final_response = client.chat.completions.create(
                model=os.getenv("GEMINI_MODEL_NAME"),
                messages= messages
            )
            return final_response.choices[0].message.content
         
    # LLM answered directly without needing a tool
    return reply.content


def main():
    tee = start_tee(__file__)
    #print("\n schema creation taking place")
    insert_data_intodb()
    # print('-' * 60)
    # print("insert completed")
    print('-' * 60)

    user_query = input("\n How can I help you with flights today? : ").strip()

    print("\n Running Database Engine ... finding best deals for you")
    answer = run_agent(user_query)

    print(answer)
    stop_tee(tee)
        
if __name__ == '__main__':
    main()


