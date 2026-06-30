
"""
LangChain Learning Path for AI Strategists

This script provides a progressive learning path through LangChain Core, LangGraph, and advanced LangChain patterns.
It's designed for Python and AI newcomers aspiring to become AI strategists/leaders, offering practical examples
and strategic insights at each stage.

Author: Manus AI
Date: Jun 20, 2026
"""

import os
from dotenv import load_dotenv

# --- Environment Setup ---
# Load environment variables from a .env file (if present)
# This is crucial for securely managing API keys without hardcoding them.
load_dotenv()

# Ensure your OpenAI API key is set as an environment variable.
# You can get one from https://platform.openai.com/account/api-keys
# Example in .env file: OPENAI_API_KEY='your_openai_api_key_here'
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("Error: OPENAI_API_KEY not found. Please set it in your environment or a .env file.")
    exit()

# --- Stage 1: LangChain Core Fundamentals ---
# LangChain Core provides the foundational components for building LLM applications.
# It focuses on modularity, allowing you to combine different components like LLMs, prompts, and output parsers.

print("\n--- Stage 1: LangChain Core Fundamentals ---")
print("Understanding the building blocks of LLM applications.")

# 1. Large Language Models (LLMs)
# The brain of our AI applications. LangChain provides a unified interface for various LLMs.
# We'll use OpenAI's ChatOpenAI model for demonstration.
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

print("\n1. Large Language Models (LLMs):")
print("   - LLMs are the core AI models that generate human-like text.")
print("   - LangChain provides a consistent interface to interact with different LLMs.")

# Initialize the LLM. The 'model' parameter specifies which OpenAI model to use.
# 'temperature' controls the randomness of the output (0.0 for deterministic, higher for creative).
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7, api_key=openai_api_key)
print(f"   - Initialized ChatOpenAI model: {llm.model_name} with temperature {llm.temperature}")

# 2. Prompts: Guiding the LLM
# Prompts are instructions or questions given to the LLM. LangChain's prompt templates
# make it easy to create dynamic prompts with placeholders.

print("\n2. Prompts: Guiding the LLM:")
print("   - Prompts are the instructions we give to the LLM.")
print("   - LangChain's `ChatPromptTemplate` allows for structured and dynamic prompts.")

# Define a simple prompt template with a placeholder for the 'topic'.
# This allows us to reuse the same prompt structure for different topics.
# The 'system' message sets the persona or general instructions for the AI.
# The 'user' message contains the specific query.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Your goal is to provide concise and informative answers."),
    ("user", "Tell me a fun fact about {topic}.")
])
print("   - Created a ChatPromptTemplate with 'system' and 'user' messages.")
print(f"     Example prompt structure: {prompt.messages}")

# 3. Output Parsers: Structuring LLM Responses
# LLMs often return raw text. Output parsers help extract and structure information
# from these responses into more usable formats (e.g., strings, JSON, Pydantic objects).

print("\n3. Output Parsers: Structuring LLM Responses:")
print("   - Output parsers convert raw LLM text responses into structured data.")
print("   - `StrOutputParser` is the simplest, converting output to a plain string.")

# The simplest parser, converting the LLM's output directly to a string.
output_parser = StrOutputParser()
print("   - Initialized StrOutputParser.")

# 4. Chains: Combining Components
# Chains are sequences of components (LLMs, prompts, parsers, other chains) that work together.
# The 'pipe' operator (`|`) is a powerful way to link these components in LangChain Expression Language (LCEL).

print("\n4. Chains: Combining Components (LangChain Expression Language - LCEL):")
print("   - Chains link LLMs, prompts, and parsers into a single, executable workflow.")
print("   - LCEL (LangChain Expression Language) uses the `|` operator for intuitive chaining.")

# Create a simple chain: prompt -> llm -> output_parser
# This chain takes a 'topic', formats the prompt, sends it to the LLM, and then parses the output.
chain = prompt | llm | output_parser
print("   - Created a chain: `prompt | llm | output_parser`.")

# --- Running the Stage 1 Chain ---
print("\n--- Running Stage 1 Example ---")
print("Let's invoke our first LangChain Core application!")

topic_to_query = "the universe"
print(f"Querying for a fun fact about: '{topic_to_query}'")

# Invoke the chain with the desired input.
response = chain.invoke({"topic": topic_to_query})
print("\nLLM Response (Stage 1):")
print(response)

print("\n--- Strategic Insight (Stage 1) ---")
print("As an AI strategist, understanding LangChain Core means recognizing the modularity of AI components.")
print("You can swap out LLMs, design better prompts, and ensure structured outputs. This flexibility is key for:")
print("1. **Cost Optimization**: Choosing the right LLM for the task (e.g., smaller models for simple tasks).")
print("2. **Performance Tuning**: Crafting precise prompts and parsers to improve accuracy and reduce hallucinations.")
print("3. **Scalability**: Building reusable components that can be easily integrated into larger systems.")
print("This foundational understanding allows you to make informed decisions about technology stack and architecture.")



# --- Stage 2: LangGraph - Building Stateful Agents ---
# LangGraph is built on top of LangChain Core and focuses on creating stateful, multi-actor applications
# with explicit control flow. It allows for cycles in the graph, enabling agents to iterate, re-evaluate,
# and make dynamic decisions, which is crucial for complex AI behaviors.

print("\n\n--- Stage 2: LangGraph - Building Stateful Agents ---")
print("Moving beyond linear chains to create dynamic, iterative AI agents.")

# 1. Key Concepts: State, Nodes, Edges
# LangGraph models agent behavior as a graph where nodes are steps, and edges define transitions.
# The 'state' is a shared data structure that flows through the graph, updated by each node.

print("\n1. Key Concepts: State, Nodes, Edges:")
print("   - **State**: The shared memory/context that nodes read from and write to.")
print("   - **Nodes**: Individual steps or functions that perform an action (e.g., call LLM, use a tool).")
print("   - **Edges**: Define the transitions between nodes, including conditional logic and loops.")

from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Define the graph state. This is what gets passed around between nodes.
# We'll keep it simple for now, just a list of messages.
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

print("   - Defined `AgentState` to hold a list of messages, representing the conversation history.")

# 2. Defining Nodes: Actions in the Graph
# Each node in LangGraph is a function that takes the current state and returns an update to it.

print("\n2. Defining Nodes: Actions in the Graph:")
print("   - Nodes are functions that take the current state and return updates.")

# Node 1: LLM Invocation
# This node will call our LLM with the current conversation history.
def call_llm(state: AgentState):
    print("   - Executing node: call_llm (Invoking LLM)")
    messages = state["messages"]
    # We'll use the same LLM and output parser from Stage 1
    response = llm.invoke(messages)
    return {"messages": [response]}

print("   - Created `call_llm` node: sends messages to LLM and returns its response.")

# 3. Building the Graph: StateGraph
# StateGraph allows us to define the nodes and edges, including entry and exit points.

print("\n3. Building the Graph: StateGraph:")
print("   - `StateGraph` is used to define the workflow, connecting nodes with edges.")

# Create a new graph instance
workflow = StateGraph(AgentState)

# Add the LLM node to the workflow
workflow.add_node("llm_node", call_llm)
print("   - Added `llm_node` to the workflow.")

# Set the entry point for the graph. This is where the execution starts.
workflow.set_entry_point("llm_node")

# Set the exit point for the graph. After the LLM responds, we end the process.
workflow.add_edge("llm_node", END)
print("   - Set `llm_node` as the entry point and `END` as the exit point.")

# Compile the graph into a runnable LangChain object.
app = workflow.compile()
print("   - Compiled the workflow into a runnable LangGraph application.")

# --- Running the Stage 2 LangGraph Agent ---
print("\n--- Running Stage 2 Example (Simple Conversational Agent) ---")
print("Let's interact with our first stateful LangGraph agent!")

user_question = "What is the capital of France?"
print(f"User: {user_question}")

# Invoke the LangGraph app with an initial message.
# The state will be updated and passed between nodes automatically.
final_state = app.invoke({"messages": [HumanMessage(content=user_question)]})

print("\nAgent Response (Stage 2):")
# The final state contains all messages. We want the last one from the AI.
for message in final_state["messages"]:
    if message.type == "ai":
        print(message.content)

print("\n--- Strategic Insight (Stage 2) ---")
print("LangGraph introduces the concept of state and explicit control flow, which is vital for:")
print("1. **Building Complex Agents**: Enabling iterative reasoning, tool use, and dynamic decision-making.")
print("2. **Reliability & Debugging**: Visualizing the flow helps in understanding agent behavior and debugging issues.")
print("3. **Human-in-the-Loop**: Facilitating interruptions, approvals, and human oversight in AI workflows.")
print("As an AI leader, leveraging LangGraph means designing more robust, transparent, and capable AI systems.")
print("It moves beyond simple Q&A to agents that can plan, act, and adapt over extended interactions.")


# --- Stage 3: Advanced LangChain Patterns & AI Strategy ---
# This stage delves into more sophisticated LangChain capabilities, particularly focusing on
# how LangGraph enables complex agentic behavior through tool use. We'll also connect these
# technical patterns to broader AI strategy considerations.

print("\n\n--- Stage 3: Advanced LangChain Patterns & AI Strategy ---")
print("Building intelligent agents with tools and understanding their strategic implications.")

# 1. Tool Calling: Extending LLM Capabilities
# LLMs are powerful, but they can be augmented with external tools (e.g., calculators, search engines,
# APIs) to perform specific tasks, access real-time information, or execute actions.

print("\n1. Tool Calling: Extending LLM Capabilities:")
print("   - Tools allow LLMs to interact with the external world, overcoming their limitations.")
print("   - Examples: web search, code execution, database queries, API calls.")

from langchain_core.tools import tool

# Define a simple calculator tool.
@tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers and returns the result."""
    print(f"   - Executing tool: multiply({a}, {b})")
    return a * b

@tool
def add(a: float, b: float) -> float:
    """Adds two numbers and returns the result."""
    print(f"   - Executing tool: add({a}, {b})")
    return a + b

tools = [multiply, add]
print(f"   - Defined simple calculator tools: {[t.name for t in tools]}")

# 2. Integrating Tools into LangGraph Agents
# To use tools, our LangGraph agent needs to:
#   a. Decide when to call a tool (LLM's role).
#   b. Execute the tool.
#   c. Incorporate the tool's output back into the conversation.

print("\n2. Integrating Tools into LangGraph Agents:")
print("   - Agents use LLMs to decide which tool to call, execute it, and process its output.")

from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode

# Create a ToolNode to run our tools.
tool_node = ToolNode(tools)
print("   - Initialized `ToolNode` to manage tool execution.")

# Update AgentState to include tool calls and tool outputs
class AgentStateWithTools(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

print("   - Updated `AgentStateWithTools` to handle tool messages.")

# Node 1: LLM with Tool Calling Capabilities
# This LLM will be configured to understand and suggest tool calls.
def call_llm_with_tools(state: AgentStateWithTools):
    print("   - Executing node: call_llm_with_tools (Invoking LLM with tools)")
    messages = state["messages"]
    # Bind tools to the LLM so it knows about them and can suggest calling them.
    response = llm.bind_tools(tools).invoke(messages)
    return {"messages": [response]}

print("   - Created `call_llm_with_tools` node: LLM can now suggest tool calls.")

# Node 2: Tool Invocation (using the prebuilt ToolNode)
print("   - Using prebuilt `ToolNode` for tool execution.")

# 3. Building the LangGraph with Conditional Edges
# Now we need to define the flow: LLM -> (Tool Call? -> Tool Execution -> LLM) -> Final Answer

print("\n3. Building the LangGraph with Conditional Edges:")
print("   - Conditional edges enable dynamic routing based on LLM decisions.")

# Define a function to decide the next step based on the LLM's response.
def should_continue(state: AgentStateWithTools):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        # If the LLM made a tool call, we need to execute the tool.
        print("   - Decision: LLM wants to call a tool.")
        return "call_tool"
    else:
        # Otherwise, the LLM has a final answer or is continuing a conversation.
        print("   - Decision: LLM has a direct response or is continuing.")
        return "end"

print("   - Defined `should_continue` function for conditional routing.")

# Create a new graph instance for our agent with tools.
agent_workflow = StateGraph(AgentStateWithTools)

agent_workflow.add_node("llm_node", call_llm_with_tools)
agent_workflow.add_node("tool_node", tool_node)

agent_workflow.set_entry_point("llm_node")

# Add conditional edge from LLM node: if tool call, go to tool_node; otherwise, end.
agent_workflow.add_conditional_edges(
    "llm_node",
    should_continue,
    {
        "call_tool": "tool_node",
        "end": END
    }
)

# After a tool is executed, the output goes back to the LLM for processing.
agent_workflow.add_edge("tool_node", "llm_node")

agent_app = agent_workflow.compile()
print("   - Compiled the LangGraph agent with tool calling capabilities.")

# --- Running the Stage 3 LangGraph Agent with Tools ---
print("\n--- Running Stage 3 Example (Agent with Calculator Tool) ---")
print("Let's ask our agent a question that requires a tool!")

math_question = "What is 123 multiplied by 456, and then add 789 to the result?"
print(f"User: {math_question}")

# Invoke the agent with the math question.
final_agent_state = agent_app.invoke({"messages": [HumanMessage(content=math_question)]})

print("\nAgent Response (Stage 3 - Final Answer):")
# Print the final AI message from the state.
for message in final_agent_state["messages"]:
    if message.type == "ai":
        print(message.content)

print("\n--- Strategic Insight (Stage 3) ---")
print("For an AI strategist, mastering advanced LangChain patterns like tool calling is about enabling:")
print("1. **Enhanced Capabilities**: Overcoming LLM limitations (e.g., math, real-time data) by integrating specialized tools.")
print("2. **Agentic Behavior**: Building autonomous systems that can reason, plan, act, and adapt to achieve goals.")
print("3. **Robustness & Accuracy**: Reducing hallucinations by grounding LLM responses in factual tool outputs.")
print("4. **Ethical AI Development**: Carefully selecting and monitoring tools to ensure responsible and safe agent operation.")
print("5. **Innovation & Competitive Advantage**: Orchestrating complex AI workflows to solve novel business problems.")
print("As an AI leader, your role is to identify opportunities for agentic solutions, curate tool ecosystems,")
print("and establish governance for these powerful, intelligent systems. This is where AI truly transforms operations.")


# --- Conclusion ---
print("\n\n--- Conclusion ---")
print("You've now walked through the core components of LangChain, the power of stateful agents with LangGraph,")
print("and advanced patterns like tool calling. This journey from basic chains to intelligent agents is fundamental")
print("for anyone looking to lead in the AI space. Keep experimenting, building, and thinking strategically!")

