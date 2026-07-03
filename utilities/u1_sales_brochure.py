''''
This is to generate business Brochure for a company, it takes website and ...
config has load_env and path and it is taking API key auto using client
tee_logger is printiong to screen and file with same name
'''

import json
from google import genai
from google.genai import errors, types
from mistralai.client import Mistral
from scraper import fetch_website_links, fetch_website_contents
import config
from IPython.display import Markdown, display, update_display
from pathlib import Path
from dotenv import load_dotenv
from tee_logger import start_tee, stop_tee
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown

console = Console(color_system=None)
tee = start_tee(__file__)
user_provided_company_name= input(" \n\n Enter name of company you want to create a brochure : ")
user_provided_url = input(" Enter the url of company of above Company : ")

client = genai.Client()
Mclient = Mistral()

model_name = "gemini-2.5-flash"
Mmodel_name = "mistral-large-latest"

link_sysetm_prompt = '''

you are provided with the list of links found on a webpage.
you are able to decide which of the links would be most relevent to include ina brochure about the company.
Such as link to about page or company page or careers/jobs page.
You should responde in JSOn format as in this example :
{
   "links": [
     {"type": "About Page", "url", "https://full.url/goes/here/about"},
     {"type": "careers page", "url", "https://full.url/careers"}
     ]
}
'''

def get_links_user_prompt(url):
    user_prompt = '''
Here are the list of urls {url} - please decide which of the links are relevent web link for the brochure of a company
respond with full HTTPS url in JSON format. Do not include like Services, email  etc 
'''
    user_prompt +="\n".join(links)
    return user_prompt

#print(" ******* Google Reponse ********")
#links = fetch_website_links("https://edwarddonner.com")
links = fetch_website_links(user_provided_url)

#print(links)
# to cleaner output marking this as comment for Now
#print(get_links_user_prompt("https://edwarddonner.com"))
# to cleaner output marking this as comment for Now

def select_relevent_links(url):
    """Attempts generation via Gemini, falling back to Mistral on 503 ServerErrors."""
    try:
        print("Attempting generation with Gemini...")
        
        # 1. Corrected config syntax using types.GenerateContentConfig
        # 2. Fixed mismatched brackets and indentation
        response = client.models.generate_content(
            model=model_name, 
            config=types.GenerateContentConfig(
                system_instruction=link_sysetm_prompt, 
                response_mime_type="application/json"
            ),
            contents=get_links_user_prompt(url=url)
        )
        result = response.text
        return result  # Added return statement
    except (errors.ServerError, errors.ClientError)  as e:
         print(f"Gemini API issue encountered (Quota or Server Error): {e}")
         print("Attempting generation with Mistral...")
         response = Mclient.chat.complete(model=Mmodel_name, messages = [
             {"role": "system", "content": link_sysetm_prompt},
             {"role": "user", "content": get_links_user_prompt(url=url)}
             ],
             response_format={"type": "json_object"}
             )
         result = response.choices[0].message.content
         links = json.loads(result)
         return links
 # to cleaner output marking this as comment for Now   
#print(select_relevent_links("https://edwarddonner.com"))
#print(select_relevent_links(user_provided_url))
# to cleaner output marking this as comment for Now
#print(response.text)
#print(" ******* into fetch_page_and_relevent_links ********")

def fetch_page_and_relevent_links(url):
    #print("\n\n 1. Fetching website content ")
    content = fetch_website_contents(url)
    #print("\n\n 2. seleting relevent links ...")
    relevent_links = select_relevent_links(url)
    result = f"## Landing Page:\\n\n{content}\n## Relevant Links: \n"
    # 1. Checking if the variable is already a dictionary/list, or if it is still a string
   
    try:
        if isinstance(relevent_links, str):
            try:
                parsed_json = json.loads(relevent_links)
                #print("\n\n 3. I am in try 2 \n")
            except:
                # it is already a dict or list from SDK
                parsed_json={}
                #print("\n\n 4. I am in except 2")
        else:
            parsed_json = relevent_links
            #print("\n\n 5. I am in else .......")

        # If it's a dictionary with a key like 'links', grab the actual list out of it
        if isinstance(parsed_json, dict) and "links" in parsed_json:
            links_list = parsed_json["links"]
            #print("\n\n 6. I am creating links_list....")
        else:
            links_list = parsed_json
            #print("\n\n 7. I am in else of is instance 118 ....")
            
    except json.JSONDecodeError as e:
        return result
        #print(fetch_page_and_relevent_links("https://huggingface.co"))
        #print(" ******* Mistral Reponse ********")
    
    for link in links_list:
            #print(f"\n\n 8. in for loop .... {link} ")
            result += f"\n\n ### Link : {link}\n"
            result += fetch_website_contents(link["url"])
            return result

#output = fetch_page_and_relevent_links("https://huggingface.co")
output = fetch_page_and_relevent_links(user_provided_url)
#print (output)

brochure_system_prompt = """
You are an assistant that analyses the content of several relevent pages for a company website and create a short brochure  about
the company for its prospective customers, partners, investors and job seekers.
Respond in markdown with code blocks.
Include details of company culture , customers amd careers/job if you have an y information.
"""

def get_brochure_user_prompt(company, url):
    user_prompt =  f""" you are looking at comapny called {company}, here are the contents of its landing page and other relevet pages.
    use this informatuon to build a short brochure for the comany in Markdown without code blocks \n\n

"""
    user_prompt = fetch_page_and_relevent_links(url)
    user_prompt = user_prompt[:5_000]
    #print("\n\n ...... inside the get brochure user prompt function ......")
    return user_prompt

#get_brochure_user_prompt("hugging face", "https://huggingface.co")
get_brochure_user_prompt(user_provided_company_name, user_provided_url)

def create_brochure(company_name, url):
    response = Mclient.chat.complete(model=Mmodel_name, messages = [
             {"role": "system", "content": brochure_system_prompt},
             {"role": "user", "content": get_brochure_user_prompt(company_name, url=url)}
             ],
             )
    result = response.choices[0].message.content
    print(f"\n\n Creating brochure for {company_name}......")
    console.print(Markdown(result))

def main():
    #print("\n\n ... starting main ....")
    create_brochure(user_provided_company_name, user_provided_url)

if __name__ == "__main__":
    main()

print(
    f"\n\n---------------------End of execution - "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}---------------------"
)

stop_tee(tee)