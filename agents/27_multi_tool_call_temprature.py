"""

A tool definition dict that describes a get_weather function to the Mistral API 
— with a city parameter as a required string
A get_weather(city) Python function that looks up the city in CITY_DB and returns a dict 
— handle the case where the city doesn't exist
A while loop that keeps calling Mistral until finish_reason == "stop" 
— printing every step so you can see what's happening"""

from pydantic import BaseModel, EmailStr, Field
import os
from dotenv import load_dotenv
from mistralai.client import Mistral


load_dotenv()

MODEL  = "mistral-small-latest"

CITY_DB = {
    "london":   {"temp_c": 12, "condition": "rainy",  "humidity": 85},
    "toronto":  {"temp_c": -3, "condition": "snowy",  "humidity": 70},
    "dubai":    {"temp_c": 38, "condition": "sunny",  "humidity": 30},
    "paris":    {"temp_c": 9,  "condition": "cloudy", "humidity": 75},
}


class cityweather(BaseModel):
    city: str = Field(description="The city for which to get weather information")
    
class compartecityweather(BaseModel):
    city1: str = Field(description="The city for which to get weather information")
    city2: str = Field(description="The city for which to get weather information")

def get_weather(city: str) -> dict:
    """Get the weather for a given city."""
    
    weather = CITY_DB.get(city.lower())
    #what CITY.DB will return if the city is not found, it will return None, so we can handle that case 
    if weather is None:
        return {"error": f"City '{city}' not found in database."}
    return weather


def comparetemperature(city1: str, city2: str) -> str:
    """Compare the temperature of two given cities."""
    
    print(f"city1 = {city1}, city2 = {city2}")
    weather1 = CITY_DB.get(city1.lower())
    weather2 = CITY_DB.get(city2.lower())
    
    if weather1 is None:
        return f"Frist City '{city1}' not found in database."
    if weather2 is None:
        return f"Second City '{city2}' not found in database."

    temp1 = weather1["temp_c"]
    temp2 = weather2["temp_c"]

    if temp1 > temp2:
        return f"{city1.title()} is warmer than {city2.title()} by {temp1 - temp2}°C."
    elif temp1 < temp2:
        return f"{city1.title()} is colder than {city2.title()} by {temp2 - temp1}°C."
    else:
        return f"{city1.title()} and {city2.title()} have the same temperature."
    
def execute_tool(tool_name: str, tool_args: dict) -> dict:
    """Execute a tool by name with the given arguments."""
    
    if tool_name == "get_weather":
        return get_weather(**tool_args)
    elif tool_name == "compare_temperature":
        return comparetemperature(**tool_args)
    else:
        return {"error": f"Tool '{tool_name}' not recognized."}

def main():
    count_loops = 0
    while True:
        count_loops += 1
        user_input = input("Enter function (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break
        
        # Here you would normally call the Mistral API with the user_input
        # For demonstration, we'll simulate a tool call based on the input
        if "weather" in user_input.lower():
            city = input("Enter city name: ").split()[-1]  # naive extraction of city name
            result = execute_tool("get_weather", {"city": city})
        elif "compare" in user_input.lower():
            cities = input("Enter two city names separated by a space: ").split()[-2:]  # naive extraction of two city names
            result = execute_tool("compare_temperature", {"city1": cities[0], "city2": cities[1]})
        else:
            result = {"error": "Command not recognized."}
        
        print("Result:", result)

    print(f"""
─────────────────────────────────────────────────────────
Lets see how many loops it did: {count_loops}
─────────────────────────────────────────────────────────
""")

if __name__ == "__main__":
    main()