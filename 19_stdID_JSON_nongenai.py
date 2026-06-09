""" 
creating student ID generator function
and adding details to the JSON files
without using langchian agent or pydantic structure
"""
import os
import json
from datetime import datetime

def student_validate_age(age):
    if age < 3 or age > 25:
        print ("Age must be between 3 and 25 years old.\n\n")
        raise ValueError("Age must be between 3 and 25 years old.")
    return age

def get_next_student_id():
    # Check if the file exists, if not create it and start with STD0001
    if not os.path.exists("19_student_records.json"):
        with open("19_student_records.json", "w") as f:
            json.dump([], f)

    # Read the current counter value
    with open("19_student_records.json", "r") as f:
        records = json.load(f)
        if records:
            last_id = records[-1]['student_id']
            last_num = int(last_id.replace("STD", "").replace("₹", ""))
            next_num = last_num + 1
            return f"STD{str(next_num).zfill(4)}"
        else:
            return "STD0001"
    
    # Increment the counter
    counter += 1
    
    # Write the updated counter back to the file
    with open("student_id_counter.txt", "w") as f:
        f.write(str(counter))
    
    # Return the new student ID in the format STD001, STD002, etc.
    return f"STD{counter}"

def register_student(name: str, age: int, course: str):
    student_id = get_next_student_id()
    student_record = {
        "student_id": student_id,
        "name": name,
        "age": student_validate_age(age),
        "course": course,
        "updated_at": datetime.now().isoformat()
    }
    
    # Append the new student record to the JSON file
    with open("19_student_records.json", "r") as f:
        records = json.load(f)
    
    records.append(student_record)
    
    with open("19_student_records.json", "w") as f:
        json.dump(records, f, indent=4)
    
    return student_record

# Example usage
if __name__ == "__main__":
    new_student = register_student(
        input("Enter student name: "), 
        int(input("Enter student age: ")), 
        input("Enter student course: "))
    
    print(new_student)
