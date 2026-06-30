'''
A tokenizer as a translator that turns human words into a secret code that AI can understand.
 A tokenizer breaks your sentence into tiny pieces called tokens (which can be whole words, 
 parts of words, or punctuation) and gives each piece a unique ID number.
 When you tell tiktoken to use cl100k_base, you are telling it: 
 "Hey, slice up my text using the exact same 100,000-piece dictionary that GPT-4 uses.
 2. tiktoken.get_encoding('cl100k_base')What it does: 
 This is the trigger. tiktoken checks a hidden cache folder on your computer to see 
 if the cl100k_base dictionary file is already there.If it is NOT there (First time): 
    It quickly connects to a public OpenAI web link, downloads the text file containing 
    the dictionary, saves it to your hard drive, and loads it into Python.
    If it IS there (Second time onwards): It instantly loads the file from your hard drive 
    into Python without using the internet.

 '''

import tiktoken

encoding = tiktoken.get_encoding('o200k_base')
tokens = encoding.encode("My name is Tehzeeb Ahmed Pasha and I would like to build a great Product")


for token_id in tokens:
    # Pass a list [token_id] 
    token_text = encoding.decode([token_id])
    print (f"{token_id} - {token_text}")