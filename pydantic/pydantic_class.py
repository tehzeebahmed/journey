from pydantic import BaseModel, Field
import json

# -------------------------------
# 1. Create a Movie Model
# -------------------------------
class Mobie(BaseModel):
    title: str = Field(max_length=100)
    year:  int
    genre: list [str]
    duration_min: int
    rating: float = 4.6, Field(ge=0.0, le=10.0)

# Instantiate using a dictionary
movie_data = {
    "title": "Sholay",
    "year": 1975,
    "genre": ["Drama", "Action"],
    "duration_min": 204
    
}

print(f"1.  porint movie data directly \n\n {movie_data}")
movie = Mobie(**movie_data)

print("========== Exercise 1 ==========")
print("Movie created from dictionary:")
print(f"2.  pyd print : {movie}")

# -------------------------------
# 2. Parse from JSON
# -------------------------------
json_movie_sting = '''
{
    "title": "3 Idiots",
    "year": 2009,
    "genre": ["Comedy", "Drama"],
    "duration_min": 170,
    "rating": 4.8
}
'''
#convert json string into pydantic structure
movie_dict = json.loads(json_movie_sting)
print(f"\n\n3.  Dictionary loaded from JSON:{movie_dict}")
print()

# Parse dictionary into Pydantic model
movie_from_json = Mobie(**movie_dict)

print("========== Exercise 2 ==========")
print("\n\n4.  Movie parsed from JSON:")
print(movie_from_json)
print()

# Convert Pydantic model back to dictionary
print("\n\n5.  As Dictionary:")
print(movie_from_json.model_dump())
print()

# Convert Pydantic model back to JSON
print("\n\n6.  As JSON:")
print(movie_from_json.model_dump_json(indent=4))