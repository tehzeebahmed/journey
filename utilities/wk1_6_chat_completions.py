'''
we are showing here the interactions are stateless.
with Gemini we pass system_intsruxctions and input and get output_text back

'''
from google import genai
import config

client = genai.Client()



response = client.interactions.create(
    model="gemini-2.5-flash", 
    system_instruction="You are an assistant AI",
    input="Hi I am Tehzeeb Pasha"
    
)
#response.output_text

print(f" the response back is : {response.output_text}")
