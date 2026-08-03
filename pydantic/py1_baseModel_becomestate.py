"""to understand how basemodel becomes a state"""

from pydantic import BaseModel

# 1. Define the notebook template (The State Structure)
class MathState(BaseModel):
    current_value: int
    steps_taken: list[str] = [] # inital empty state

# 2. Step 1: An addition function that updates the state
def add_five(state: MathState) -> MathState:
    state["current_value"] += 5
    state["steps_taken"].append("Added 5")
    return state

# 3. Step 2: A multiplication function that reads and updates the state
def multiply_by_three(state: MathState) -> MathState:
    state["current_value"] *= 3
    state["steps_taken"].append("Multiplied by 3")
    return state

# 4. Orchestration: Create the live state and pass it through the pipeline
def main():
    # Initial state setup
    my_state: MathState = {
        "current_value": 10,
        "steps_taken": ["Started with 10"]
    }
    
    # Run the math pipeline
    my_state = add_five(my_state)           # 10 + 5 = 15
    my_state = multiply_by_three(my_state)  # 15 * 3 = 45
    
    print(f"Final Value: {my_state['current_value']}")
    print(f"History Log: {my_state['steps_taken']}")

if __name__ == "__main__":
    main()
