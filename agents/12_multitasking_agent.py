# this is multi conversational agent which will take mukltiple inputs
# and will refine its output accordingly 

"""
ultitasking conversational agent that includes:

Building prompts
Generating responses (simulated here)
Parsing outputs
Executing actions
Memory management
Robust error handling with retries
"""


import time
import json
from datetime import datetime

class ConversationalAgent:
    def __init__(self, max_retries=3, retry_delay=1):
        """
        Initialize the agent with retry parameters and empty memory.
        Inputs:
          max_retries (int): Number of retry attempts for operations.
          retry_delay (int): Delay in seconds between retries.
        Outputs:
          None
        """
        self.memory = {"conversations": []}  # Stores conversation history
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def build_prompt(self, user_input):
        """
        Build a prompt for the LLM based on user input.
        Inputs:
          user_input (str): The user's message.
        Outputs:
          prompt (str): The formatted prompt string.
        """
        prompt = f"User says: {user_input}\nAgent, please respond appropriately."
        return prompt

    def generate_response(self, prompt):
        """
        Simulate generating a response from an LLM with retries.
        Inputs:
          prompt (str): The prompt to send to the LLM.
        Outputs:
          response (str): The generated response text or error message.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                # Simulate LLM call (replace with actual API call)
                response = f"Simulated response to: {prompt}"
                return response
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    return f"Error generating response: {str(e)}"
                time.sleep(self.retry_delay)

    def parse_response(self, response):
        """
        Parse the LLM response to extract actionable info.
        Inputs:
          response (str): The raw response text.
        Outputs:
          parsed (dict): Parsed data or error info.
        """
        try:
            # For demo, parse response as JSON if possible
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # If not JSON, return raw text wrapped in dict
            parsed = {"text": response}
        return parsed

    def execute_action(self, parsed_data):
        """
        Execute an action based on parsed data.
        Inputs:
          parsed_data (dict): Parsed response data.
        Outputs:
          result (str): Result of the action.
        """
        # Example action: echo back the text or handle commands
        if "text" in parsed_data:
            return f"Action executed: echoing '{parsed_data['text']}'"
        else:
            return "No actionable content found."

    def update_memory(self, user_input, response, action_result):
        """
        Update conversation memory with new interaction.
        Inputs:
          user_input (str): User's message.
          response (str): Agent's response.
          action_result (str): Result of executed action.
        Outputs:
          None
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_input": user_input,
            "response": response,
            "action_result": action_result
        }
        self.memory["conversations"].append(entry)

    def converse(self, user_input):
        """
        Full conversation cycle: build prompt, generate, parse, execute, update memory.
        Inputs:
          user_input (str): User's message.
        Outputs:
          final_output (dict): Contains response, action result, and memory snapshot.
        """
        prompt = self.build_prompt(user_input)  # Build prompt from input
        response = self.generate_response(prompt)  # Generate LLM response
        parsed = self.parse_response(response)  # Parse the response
        action_result = self.execute_action(parsed)  # Execute action based on parsed data
        self.update_memory(user_input, response, action_result)  # Update memory with interaction

        return {
            "response": response,
            "action_result": action_result,
            "memory": self.memory
        }

def main():
    """
    Main function to run the conversational agent interactively.
    Inputs:
      None (reads user input from console)
    Outputs:
      None (prints agent responses and memory)
    """
    agent = ConversationalAgent()  # Create agent instance
    print("Conversational Agent started. Type 'exit' to quit.")

    while True:
        user_input = input("You: ")  # Read user input
        if user_input.lower() == "exit":
            print("Exiting agent. Goodbye!")
            break

        result = agent.converse(user_input)  # Run conversation cycle
        print("Agent response:", result["response"])  # Show response
        print("Action result:", result["action_result"])  # Show action result
        print("Memory snapshot:", json.dumps(result["memory"], indent=2))  # Show memory

if __name__ == "__main__":
    main()
    