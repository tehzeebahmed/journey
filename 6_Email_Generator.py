"""
### **Project 3: Email Generator**
**Difficulty**: ⭐
**Time**: 45 mins
**Concepts**: PromptTemplate, multiple variables, tone

**Description**:
Generate professional emails for different scenarios with customizable tone.

**Inputs**:
- recipient_name: str
- purpose: str (meeting request, complaint, follow-up, etc.)
- tone: str (formal, friendly, assertive)
- context: str

**Features**:
- Generate subject line + email body
- Different tones: formal, friendly, assertive
- Multiple email variants
- Grammar and tone validation

**Example**:
```
Recipient: Sarah
Purpose: Meeting Request
Tone: Formal

Subject: Request for Meeting - Project Discussion
Body:
Dear Sarah,
I hope this email finds you well. I would like to schedule a meeting at your earliest 
convenience to discuss the upcoming project...
```

**Implementation Hints**:
```python
subject_prompt = PromptTemplate.from_template(...)
body_prompt = PromptTemplate.from_template(...)

# Generate both subject and body
```
"""

import os
import logging
from typing import Dict
from dotenv import load_dotenv
from langchain_google_genai  import GoogleGenerativeAI, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, ChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

def logger_setup():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    print("\n" + "="*70)
    print(logger.name.center(70))
    print("="*70 + "\n")
    return logger
   # Print the logger's name centered within 70 characters as a header

def Check_API_Key(logger):
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
    else:
        logger.info("GEMINI_API_KEY found and loaded successfully.")

def email_generator(logger):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        timeout=60
    )
    logger.info("Email Generator initialized successfully.")
    # to get clean output without extra metadata, we can use StrOutputParser to extract just the text response from the LLM output
    llm = llm | StrOutputParser()
    return llm        

if __name__ == "__main__":
    logger = logger_setup()
    Check_API_Key(logger)
    llm = email_generator(logger)
    # Example usage
    
    recipient_name = input("Enter recipient's name: \n")
    purpose = input("Enter the purpose of the email: \n")
    tone = input("Enter the tone of the email (formal, friendly, assertive): \n")
    context = input("Enter any additional context for the email: \n")
    print(f"\n\nReceived recipient_name: '{recipient_name}', purpose: '{purpose}', tone: '{tone}', context: '{context}'")  # Debug print
    
    subject_prompt = PromptTemplate.from_template(
        "Generate a professional email subject line for an email to {recipient_name} " \
        "with the purpose of {purpose} in a {tone} tone."
    )
    
    body_prompt = PromptTemplate.from_template(
        "Generate a professional email body for an email to {recipient_name} " \
        "with the purpose of {purpose} in a {tone} tone. Include the following context: {context}"
    )
    
    subject = llm.invoke(
        subject_prompt.format(
            recipient_name=recipient_name, 
            purpose=purpose, 
            tone=tone))
    
    body = llm.invoke(
        body_prompt.format(
            recipient_name=recipient_name, 
            purpose=purpose, 
            tone=tone, 
            context=context))
    
    print("\nGenerated Email:")
    print("\nSubject:", subject)
    print("\nBody:", body)





