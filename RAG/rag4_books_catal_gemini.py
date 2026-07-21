
import os
import sys
import json
from pathlib import Path
import chromadb
import config
import hashlib
from tee_logger import start_tee, stop_tee
from datetime import datetime
from google import genai
from chromadb.api.types import Embeddings, EmbeddingFunction, Documents

JSON_BOOK_C = "books_catalogue.json"
DB_PATH = "./local_vectordb"
HASH_FILE = "bookscatalog_hash.txt"
api_key = os.getenv("GEMINI_API_KEY")
# all books and their details in bookscatalogue
COLLECTION_NAME = "bookscatalogue"
CURR_PATH = Path(__file__).parent
CURR_DIR_PATH = CURR_PATH
curr_file_path, filename = os.path.splitext(__file__)
# to store hash to check if json file changed or not
CURR_PATH = CURR_PATH.joinpath(JSON_BOOK_C)
# saving hash file in the same directory as json data file
HASH_FILE_PATH = CURR_DIR_PATH.joinpath(HASH_FILE)
print(f"\nDirectory - new HASH file path: {HASH_FILE_PATH}")
N_QUERY_RESULTS = 5

class customEmbedding_fn(EmbeddingFunction):
    def __init__(self) -> None:
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_EMBEDDING_MODEL")

    def __call__(self, input: Documents) -> Embeddings:
        """ core conversion engine """    
        embeddings_data = []
        print("\nembeddings are zero")
        for text in input:
            response = self.client.models.embed_content(
            model = self.model_name,
            contents= text
        )
            embeddings_data.append(response.embeddings[0].values)
        print("\nembeddings are added up")

        return embeddings_data

def get_datafile_hash(filePath:str):
    """converting to MD5 format for checking state of file"""
    with open(filePath, "rb") as file:
        return hashlib.md5(file.read()).hexdigest()
    
def initiate_dbchroma_instance(path: str) -> chromadb.PersistentClient:
    """ initiates the chromadb instance"""
    print("\nStep 1 - initializing books catalogue instance")
    return chromadb.PersistentClient(path=Path)

embedding_function=customEmbedding_fn()
def delete_and_create_db_collection(client: chromadb.PersistentClient, collection_name: str) -> chromadb.PersistentClient:
    """refreshes the database everytime and creates a new collection for use from json file"""
    print(f"\nStep 2 - Initializing the catalogue {COLLECTION_NAME}...wait for few seconds..")
    current_hash_status = get_datafile_hash(HASH_FILE_PATH)
    print("after")
    file_changed = False
    with open(HASH_FILE_PATH, "r") as file:
        if file.read().strip != current_hash_status:
            file_changed = True
    print(f"\n HASH File Status - {file_changed}")
    try:
        if file_changed:
            client.delete_collection(name= collection_name)
            print(f"\ncollection {collection_name} has been cleared..initializing again..")
    except KeyError:
        print(f"\n collection {collection_name} does not found -- try?")
    except Exception as e:
        print(f"There are errors - {e}", file=sys.stderr)
    collection = client.get_or_create_collection(name=collection_name, embedding_function = embedding_function)
    total_records = collection.count()
    print(f"\nTotal records in existing movie description database are : {total_records}")
    return collection
    
def prepare_books_catalogue(collection: chromadb.Collection):
    """ inserting data to the chroma db from json file"""
    print("Step 4 - preparing books catalogue ...")
    if os.path.exists(CURR_PATH):
        with open(CURR_PATH, "r") as file:
            books_collection = json.load(file)
            book_ids = [str(d["id"]) for d in books_collection]
            documents = [d["description"] for d in books_collection]
            metadatas=[
                {
                        "title": d["title"], 
                        "genre": d["genre"]
                } for d in books_collection]
            
            collection.add(ids=book_ids, documents=documents, metadatas= metadatas)
        # For re-using hash next time
        current_hash_status = get_datafile_hash(HASH_FILE_PATH)
        with open(HASH_FILE, "w") as f:
            f.write(current_hash_status)
    print("\n....... Document insertion complete .......")
    total_records = collection.count()
    print(f"\nTotal records in existing movie description database '{collection.name}' are : {total_records}")

def query_books_catalog(collection: chromadb.Collection, n_results: int):
    """ query engine for books catalog"""
    print("\nStep 5. Querying the database..")
    query_text = input("\nwhat is on your mind to read today: ")

    if not query_text .strip():
        print("Query cannot be empty. Please enter a valid query.", file=sys.stderr)
        return
    
    print(f"...Querying ...: {query_text} for top {n_results} results")
    results = collection.query(query_texts=[query_text], n_results=n_results)# Bring back the best 5 match

    if results and results["ids"] and results["ids"][0]:
        print("\n ------ query results ------")
        for i in range(len(results['ids'][0])):
            match_id = results['ids'][0][i]
            doc_text = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            title = metadata.get('title')
            genre = metadata.get('genre', 'N/A')# Provides 'N/A' if 'genre' key is missing
            year = metadata.get('year')
            distance = results["distances"][0][i]
            print(f"\nRank = {i +1}: Match Id: {match_id} Title: {title} Description: {doc_text} Genre: {genre} released in {year} Distance: {distance}")
            print("-----------------------")
    else: 
        print("\n No results fiound for your query ")

def main():
    """main function to run the chromadb functions"""
    now = datetime.now()
    tree_stream = None
    try:
        tree_stream = start_tee(__file__)
        client = initiate_dbchroma_instance(DB_PATH)

        collection = delete_and_create_db_collection(client, COLLECTION_NAME)

        prepare_books_catalogue(collection )
        query_books_catalog(collection, N_QUERY_RESULTS)

    except Exception as e:
        print(f"\n an unhandled exception occurred durinf script execution - {e}", file = sys.stderr)
    finally:
        if tree_stream:
            stop_tee(tree_stream)
    # print(f"Script execution ends - {datetime.now().strftime('%Y-%m-%d - %H:%M:%S')}\n")
    
    formatted_string = now.strftime("Execution ends - %Y-%m-%d - %H : %M : %S")

    print(formatted_string)

if __name__ == "__main__":
    main()

    """
    
TEST CASES -> -> -> 
    
Query                                            What you should expect
--------------------------------------------     ---------------------------------------------------
“I procrastinate and can’t stay disciplined.”  -  Atomic Habits, Deep Work, The Power of Habit
“I want to become a better software engineer.” - Clean Code, Code Complete, The Pragmatic Programmer
“A detective solving impossible murders.”      - Sherlock Holmes, Murder on the Orient Express
“Books about dragons and magic.”               - Eragon, Harry Potter, The Hobbit
“How can I become mentally stronger?”          - Can't Hurt Me, Meditations, Man's Search for Meaning
“Understanding the universe and stars.”        - Cosmos, Astrophysics for People in a Hurry
“Learning to invest my money wisely.”          - The Intelligent Investor, Psychology of Money
“How do startups become successful?”           - The Lean Startup, Zero to One
    """