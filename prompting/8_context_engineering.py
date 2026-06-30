"""
this python code is for showcasing how to use context engineering with Gemini models using langchain integration.
Context engineering is the practice of designing and structuring the input provided to a language model in a way that maximizes its understanding and relevance to the task at hand.
In this code, we are collecting various pieces of context from the user, such as the system
role, target audience, tone, previous context, and external knowledge. We then construct a prompt that incorporates all of this information to guide the Gemini model in generating a response that is tailored to the specified context.
The prompt is designed to clearly communicate the user's requirements and expectations to the model, which can help
improve the quality and relevance of the generated output. By using context engineering, we can leverage the capabilities of Gemini models more effectively and produce responses that are better aligned with the user's needs.



"""

import os
# from tempfile import template
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# load  API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#Initiate the Gemini model (langchain)
llm = ChatGoogleGenerativeAI ( model ="gemini-2.5-flash", api_key=GEMINI_API_KEY)
# in llm we are creating an instance of the ChatGoogleGenerativeAI class, w
# hich is a wrapper around the Gemini model provided by Google.
# usage of this llm will be to generate responses based on the prompts we create using the PromptTemplate class from langchain_core.prompts.
# The model specified is "gemini-2.5-flash", which is a specific version of the Gemini model optimized for fast responses. The API key is passed to authenticate our requests to the Gemini API.
# exampls llm.invoke("What is the capital of France?") will return "Paris" as the response from the Gemini model.
# or llm.predict("What is the capital of France?") will also return "Paris" as the response from the Gemini model.
# or we can use llm.generate(["What is the capital of France?", "What is the largest mammal?"]) to get responses for both questions in a single call, which will return "Paris" and "The blue whale" respectively.

print("\n Gemini context Engineering with langchain integration \n")

# colect context and question from user
topic = input("Enter your topic to explain for Gemini: ")  
system_role = input("Enter system role for Gemini (e.g. tutor/scientist/assistant): ")
audience = input("Enter target audience (e.g. children/college students/general public): ")
tone = input("Enter tone for Gemini response (e.g. friendly/formal/expert): ")
previous_context = input("Enter any prev context or information Gemini (optional): ")
external_info = input("Extra domain knowledge (optional):")
format_instructions = input("output Format /JSON/bullet (optional):")

print("\n generating advanced output using context engineering ...\n")

# build  context engineeirng prompt
prompt_template = """
you are :{system_role},
Audiance Type: {audience},
Tone style: {tone}

previous_context:
{previous_context}

external_knowledge:
{external_info}

formatting_instructions:
{format_instructions}

your goal:
Explain the following topic clearly and and accurately using the principles of context engineering.

topic:
{topic}

now produce the best anwer possible
"""
# in this prompt template, we are defining a structured format for the input that we will provide to the Gemini model. The template includes placeholders for various pieces of context that we have collected from the user, such as the system role, audience type, tone style, previous context, external knowledge, and formatting instructions. By filling in these placeholders with the actual values provided by the user, we can create a comprehensive prompt that guides the Gemini model to generate a response that is tailored to the specific context and requirements of the user.
# The prompt is designed to clearly communicate the user's needs and expectations to the model, which can help improve the relevance and quality of the generated output. By using this structured approach to prompt engineering, we can leverage the capabilities of the Gemini model more effectively and produce responses that are better aligned with the user's goals.
# The final prompt is then passed to the llm.invoke() method to generate the response from the Gemini model based on the provided context.

prompt = PromptTemplate(
    input_variables=[
        "system_role",
        "audience",
        "tone",
        "previous_context",
        "external_info",
        "format_instructions",
        "topic"
    ], 
    template=prompt_template, 
)
# here prompt is an instance of the PromptTemplate class, which is used to create a structured prompt based on the defined template. The input_variables parameter specifies the placeholders that will be filled with actual values when we format the prompt. The template parameter contains the string template that defines how the input variables will be arranged and presented to the Gemini model.
# does it use the prompt template to generate a response from the Gemini model? No, the prompt template is just a blueprint for how the input will be structured. To generate a response, we need to format the prompt with actual values and then pass it to the llm.invoke() method.
# because the prompt is defined as a PromptTemplate, we can easily format it with the user inputs to create a final prompt that is ready to be sent to the Gemini model for response generation.


# format the prompt with user inputs
final_prompt = prompt.format(
    system_role=system_role,
    audience=audience,
    tone=tone,
    previous_context=previous_context or "none provided",
    external_info=external_info or "none provided",
    format_instructions=format_instructions or "Free text",
    topic=topic
)
# in this step, we are taking the prompt template that we defined earlier and filling in the placeholders with the actual values provided by the user. The prompt.format() method is used to replace the placeholders in the template with the corresponding values from the user input. If any of the optional inputs (previous_context, external_info, format_instructions) are not provided by the user, we default them to "none provided" or "Free text" to ensure that the prompt is complete and can be processed by the Gemini model without any missing information.
# The resulting final_prompt is a fully formatted string that incorporates all the context and instructions specified by the user, and it is ready to be sent to the Gemini model for generating a response.
# By using this approach, we can ensure that the Gemini model receives a well-structured and context-rich prompt, which can help improve the relevance and quality of the generated output.

# call the model
response = llm.invoke(final_prompt)
# here we are calling the llm.invoke() method with the final_prompt that we just formatted. This method sends the prompt to the Gemini model and returns the generated response based on the provided context and instructions. The response will be tailored to the specific requirements and context that we included in the prompt, allowing us to get a more relevant and accurate answer from the model.
# The response object may contain various attributes, but we are specifically interested in the content of the response, which can be accessed using response.content. This will give us the actual text generated by the Gemini model based on our prompt.
# Finally, we print the content of the response to see the output generated by the Gemini model based on our context engineering prompt.

#print response
print(response.content)