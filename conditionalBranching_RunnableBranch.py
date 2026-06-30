# example inspired by the 
# demonstration on implementing conditional routing with Runnable Branch, 
# explaining each library and line of code clearly.

# Importing necessary libraries and modules

# dotenv helps us load environment variables from a .env file securely.
# This way, sensitive info like API keys are not hard-coded in the script.
from dotenv import load_dotenv

# os module allows us to interact with the operating system,
# here we use it to access environment variables.
import os

# Import Gemini SDK from Google's official package to interact with the Gemini AI model.
# This SDK lets us send prompts and receive generated responses.
from langchain_google_genai import ChatGoogleGenerativeAI

# Import core runnable tools from LangChain to build our workflow.
# RunnableLambda wraps Python functions to make them runnable in the chain.
# RunnableParallel runs multiple steps side-by-side, passing all outputs forward.
# RunnableBranch enables conditional routing based on logic we define.
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnableBranch

# Load environment variables from the .env file into the system environment.
load_dotenv()

# Retrieve the Gemini API key from environment variables.
# This key is required to authenticate requests to Gemini.
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Check if the API key exists; if not, stop the program with an error.
if not gemini_api_key:
    raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY in your environment.")

# Print the model name we will use for clarity.
model_name = "gemini-1"
print(f"Using model: {model_name}")

# Initialize the Gemini client with the API key.
# This client will be used to send prompts and get responses.
client = ChatGoogleGenerativeAI(api_key=gemini_api_key, model=model_name)

# Define a helper function to send a prompt to Gemini and return the generated text.
def call_gemini(prompt: str) -> str:
    # Send the prompt to Gemini using the client.
    response = client.invoke(prompt)
    # Return only the generated text from the response.
    return response.text

# Define a function to collect and normalize user inputs.
def collect_inputs(user_input: dict) -> dict:
    # Extract ticket description and urgency choice from user input.
    ticket_text = user_input.get("ticket")
    urgency_choice = user_input.get("urgency")

    # Map numeric urgency choice to a descriptive label.
    urgency_map = {1: "high", 2: "medium", 3: "low"}
    urgency_label = urgency_map.get(urgency_choice, "low")

    # Return a clean dictionary with structured data.
    return {"ticket": ticket_text, "urgency": urgency_label}

# Wrap the collect_inputs function in a RunnableLambda to make it part of the workflow.
CollectorRunnable = RunnableLambda(collect_inputs)

# Define a RunnableParallel to pass multiple pieces of data forward simultaneously.
# This keeps all relevant context available for branching decisions.
ParallelStage = RunnableParallel(lambda inputs: (inputs["ticket"], inputs["urgency"], inputs))

# Define handlers for each urgency level, wrapped in RunnableLambda.

# High urgency handler: creates a prompt for critical issues needing immediate attention.
def high_urgency_handler(inputs: dict) -> str:
    prompt = (
        f"Attention on-call engineer! Critical issue reported:\n"
        f"{inputs['ticket']}\n"
        "This is a production-impacting problem requiring immediate action."
    )
    return call_gemini(prompt)

HighUrgencyRunnable = RunnableLambda(high_urgency_handler)

# Medium urgency handler: creates a friendly customer-facing email acknowledging the issue.
def medium_urgency_handler(inputs: dict) -> str:
    prompt = (
        f"Dear customer, we received your ticket:\n"
        f"{inputs['ticket']}\n"
        "Our team is investigating and will update you shortly."
    )
    return call_gemini(prompt)

MediumUrgencyRunnable = RunnableLambda(medium_urgency_handler)

# Low urgency handler: generates a polite acknowledgement for minor issues or feature requests.
def low_urgency_handler(inputs: dict) -> str:
    prompt = (
        f"Thank you for your feedback:\n"
        f"{inputs['ticket']}\n"
        "We appreciate your input and will consider it for future improvements."
    )
    return call_gemini(prompt)

LowUrgencyRunnable = RunnableLambda(low_urgency_handler)

# Define condition functions to decide which branch to take based on urgency.
def is_high(inputs: dict) -> bool:
    return inputs.get("urgency") == "high"

def is_medium(inputs: dict) -> bool:
    return inputs.get("urgency") == "medium"

# Create a RunnableBranch that routes input to the correct handler based on urgency.
TicketRouter = RunnableBranch(
    branches=[
        (is_high, HighUrgencyRunnable),
        (is_medium, MediumUrgencyRunnable)
    ],
    default=LowUrgencyRunnable  # Default to low urgency if no other condition matches.
)

# Assemble the full workflow by chaining the steps.
# Input -> Collect and normalize -> Parallel pass -> Branch routing
workflow = CollectorRunnable | ParallelStage | TicketRouter

# Main program block to run the workflow.
if __name__ == "__main__":
    # Prompt user to enter a support ticket description.
    ticket = input("Enter support ticket description: ")

    # Prompt user to select urgency level.
    print("Select urgency level: 1 (High), 2 (Medium), 3 (Low)")
    urgency = int(input("Enter urgency (1-3): "))

    # Bundle inputs into a dictionary.
    user_input = {"ticket": ticket, "urgency": urgency}

    # Run the workflow with the user input.
    response = workflow.invoke(user_input)

    # Print the generated response tailored to the urgency.
    print("\nGenerated Response:")
    print(response)


"""

### Explanation Summary:
- We start by securely loading environment variables to keep sensitive info safe.
- We use the Gemini SDK to interact with the AI model for generating text.
- LangChain's runnable tools help us build a flexible workflow:
  - `RunnableLambda` wraps Python functions to be part of the chain.
  - `RunnableParallel` passes multiple pieces of data forward simultaneously.
  - `RunnableBranch` routes the workflow based on conditions.
- The workflow collects user input, normalizes it, then routes it to different handlers depending on urgency.
- Each handler creates a prompt tailored to the urgency and calls Gemini to generate a response.
- Finally, the program runs interactively, showing how the workflow adapts dynamically.


"""