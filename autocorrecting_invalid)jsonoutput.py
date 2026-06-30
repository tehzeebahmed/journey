# a real-life example of a Python script t
# hat auto-corrects invalid JSON outputs, 
# similar to the concept in the video. T
# his example will include the libraries used, why we use them, 
# and a detailed explanation of each line to help you understand the process clearly.

"""---
### Real-Life Example: Auto-Correcting Invalid JSON Outputs in a Data Processing Pipeline

Imagine you work in a data analytics team 
where you receive JSON data from various sources, 
but sometimes the JSON is malformed or doesn't follow the expected structure. 
You want to automatically fix these JSON errors and validate the data 
before processing it further.

---

### Python Script Example

"""

import json  # To parse and handle JSON data
from pydantic import BaseModel, ValidationError  # For data validation and schema enforcement
from typing import List  # To define list types in data models

# Define the expected data model using Pydantic
class DailyScheduleItem(BaseModel):
    day: int
    focus_topic: str
    estimated_hours: float
    tasks: List[str]

class StudyPlan(BaseModel):
    student_name: str
    goal: str
    duration_days: int
    topics: List[str]
    daily_schedule: List[DailyScheduleItem]

def strip_markdown_fences(text: str) -> str:
    """
    Removes triple backtick markdown fences if present.
    """
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        return "\n".join(lines[1:-1])
    return text

def auto_correct_json(bad_json: str) -> str:
    """
    Attempts to fix common JSON issues like trailing commas or missing brackets.
    This is a simple example; in real cases, you might use an LLM or more complex logic.
    """
    # Example fix: remove trailing commas before closing brackets
    corrected = bad_json.replace(",}", "}").replace(",]", "]")
    return corrected

def parse_and_validate(json_text: str) -> StudyPlan:
    """
    Parses JSON text, validates it against the StudyPlan model,
    and attempts auto-correction if validation fails.
    """
    try:
        # Strip markdown fences if any
        clean_text = strip_markdown_fences(json_text)
        # Parse JSON
        data = json.loads(clean_text)
        # Validate data structure
        plan = StudyPlan(**data)
        print("JSON parsed and validated successfully!")
        return plan
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error detected: {e}")
        print("Attempting to auto-correct JSON...")
        # Try to auto-correct the JSON string
        fixed_json = auto_correct_json(clean_text)
        try:
            data = json.loads(fixed_json)
            plan = StudyPlan(**data)
            print("JSON auto-corrected and validated successfully!")
            return plan
        except (json.JSONDecodeError, ValidationError) as e2:
            print(f"Auto-correction failed: {e2}")
            raise

# Example usage with broken JSON input
broken_json = """
{
    "student_name": "Alice",
    "goal": "Learn Python",
    "duration_days": 5,
    "topics": ["Basics", "Data Structures", "OOP",],
    "daily_schedule": [
        {"day": 1, "focus_topic": "Basics", "estimated_hours": 2, "tasks": ["Variables", "Loops",]},
        {"day": 2, "focus_topic": "Data Structures", "estimated_hours": 3, "tasks": ["Lists", "Dictionaries"]}
    ],
}
"""

if __name__ == "__main__":
    study_plan = parse_and_validate(broken_json)
    print(study_plan)

"""

---

### Explanation of Libraries and Code

- **json**: This standard Python library is used to parse JSON strings into Python dictionaries and vice versa. It's essential for handling JSON data.

- **pydantic**: This library helps define data models with type annotations and validates incoming data against these models. It ensures the JSON data matches the expected structure, catching errors early.

- **typing.List**: Used to specify that certain fields in the data model are lists, improving type safety and clarity.

---

### Line-by-Line Explanation

- **Data Models (DailyScheduleItem, StudyPlan)**: These classes define the expected JSON structure. For example, `StudyPlan` expects fields like `student_name`, `goal`, and a list of `daily_schedule` items, each validated by `DailyScheduleItem`.

- **strip_markdown_fences**: Sometimes, JSON output from models or APIs includes markdown code fences (```), which are not valid JSON. This function removes those fences to clean the input.

- **auto_correct_json**: A simple function that fixes common JSON mistakes like trailing commas before closing braces or brackets, which cause parsing errors.

- **parse_and_validate**: This is the core function that:
  - Cleans the input JSON string.
  - Attempts to parse it with `json.loads`.
  - Validates the parsed data against the `StudyPlan` model.
  - If parsing or validation fails, it tries to auto-correct the JSON and validate again.
  - Raises an error if all attempts fail.

- **broken_json**: An example JSON string with common errors like trailing commas, which would normally cause parsing to fail.

- **Main block**: Runs the `parse_and_validate` function on the example JSON and prints the validated study plan.

---

### Why This Example Is Relevant

- It mirrors the real-world scenario where data from external sources can be imperfect.
- Shows how to combine JSON parsing, schema validation, and auto-correction to build robust data pipelines.
- Demonstrates practical use of libraries like Pydantic for validation, which is a key concept in the video.
- Helps you understand how to handle errors gracefully and improve data quality automatically.

---


"""