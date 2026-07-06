"""
Airline ticketing assistant using SQLite.
 
Agent flow:
[ User asks for price ]
        |
        v
[ get_ticket_price() tool — queries SQLite ]
        |
        v
[ Result passed to LLM as context ]
        |
        v
[ LLM gives friendly natural language answer ]
"""
 
import sqlite3
from llm_router import chat
import config
from tee_logger import start_tee, stop_tee
from datetime import datetime
from pathlib import Path

tee = start_tee(__file__)

script_dir = Path(__file__).resolve().parent
project_root = script_dir
db = "prices.db"

SYSTEM_PROMPT =     "You are a helpful airline ticketing assistant. "\
    "You have access to a database of ticket prices. "\
    "When given a city and its price, respond in a friendly one-line answer. "\
    "If the price is not available, politely say so and suggest the user try another city."
# ── Database setup ─────────────────────────────────────────────────────────────
def insert_data_intodb():
    """Create table and insert seed data if not already present."""
    # list of entries 
    new_cities = [
        ("Delhi", 101),
            ("tokyo", 538),
            ("London", 487),
            ("Moradabad", 235),
            ("Pune", 123)
        ]
        # with sqlite3 as conn:
    with sqlite3.connect("prices.db") as conn:
         
         conn.execute( """CREATE TABLE IF NOT EXISTS prices (city  TEXT PRIMARY KEY, price INTEGER) """)
         conn.executemany("INSERT OR IGNORE INTO prices (city, price) values(?, ?)", new_cities)
         conn.commit()
    print(f"[db] Database ready: {db}")
    conn.close()

# ── Tool: query the database ───────────────────────────────────────────────────
def get_ticket_prices(city: str)-> str:
    """
    Looks up the ticket price for a city from SQLite.
    Returns the price as a string, or 'not available'.
    """
    print(f" Database tool called for city - {city}", flush = True)
    with sqlite3.connect(db) as conn:
        cursor = conn.execute('SELECT price FROM prices where city = ? COLLATE NOCASE', (city,))
        result = cursor.fetchone()
        
        if result:
            return f"${result[0]}" 
        
        else:
            return "not available" 
    
def ask_agent(city: str):
        """
    Agent flow:
    1. Call the tool (database) to get the price
    2. Pass the tool result to the LLM as context
    3. LLM gives a natural language answer
    """
        #step 1- call the tool
        price = get_ticket_prices(city)
        # print (f" Price fetched by tool is - {price}")

        #Step 2 - build the message with tool as context
        messages = [
             {"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": f" what is the price for this city {city}"},
             {"role": "assistant", "content": f" chekced the price of this city and that is {price}"},
             {"role": "user", "content": "Please give me friend;y response with this information"}
        ]
        #step3 - LLM called 
        reply = chat(messages)
        return(reply)
            
def main():
    insert_data_intodb() 
    city = input("where do you want to travel to : ")
    reply = ask_agent(city)
    print(f" {'-' * 60}")
    print(f"\n  {reply}")
if __name__ == '__main__':
    main()        

print(
    f"\n\n---------------------End of execution - "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}---------------------"
)
