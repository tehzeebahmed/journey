"""
### **Flow of the Script (Step-by-Step for Corrected Version)**

**Step 1: initialize mistral model
* to use the better enbedding model as Chroma's default model has a very small "brain" (384 dimensions). 

**Step 2: Start Logging and Initialize ChromaDB Client**
*   `start_tee(__file__)` is called to begin logging all console output to a file (e.g., `your_script_name.log`) in addition to displaying it on the console.
*   The `initialize_chroma_client()` function is called, which creates an instance of `chromadb.PersistentClient`. This client is configured to store its data in a local directory specified by `DB_PATH` (`./local_vectordb`), ensuring data persistence.

**-NOT IMPLEMENTED THIS TIME --Step 2: Manage ChromaDB Collection**
*   The `get_or_create_movie_collection()` function is executed.
*   It first attempts to delete the collection named `COLLECTION_NAME` (`"movie_descriptions"`).
    *   If the collection exists, it's deleted, effectively clearing any previous data.
    *   If it doesn't exist (raising a `KeyError`), a message is printed, and the script proceeds without error.
*   Then, `client.get_or_create_collection()` is called to ensure the collection exists and is ready for use.
*   The current count of records in the (potentially newly created or emptied) collection is displayed.

**Step 3: Prepare Movie Data**
*   The `prepare_movie_data()` function returns a list of dictionaries. Each dictionary represents a movie and contains:
    *   A unique `id` (e.g., "id1").
    *   The `text` description of the movie.
    *   A `meta` dictionary containing structured metadata like `genre`, `certificate`, and `year`. (Crucially, `year` is now part of `meta`, and the typo `cretificate` is corrected to `certificate`).

**Step 4: Add Documents to Collection**
*   The `add_documents_to_collection()` function is called.
*   It takes the prepared list of `documents` and efficiently adds them to the ChromaDB `collection`.
*   The `ids`, `documents` (text), and `metadatas` (the `meta` dictionary for each document) are extracted using list comprehensions and passed to ChromaDB.
*   ChromaDB internally generates vector embeddings for the `documents` (text) and stores them alongside the `ids` and `metadatas`.
*   A confirmation message is printed, followed by the total count of records in the collection after the insertion.

**Step 5: Query the Database**
*   The `query_collection()` function prompts the user to enter a movie-related query.
*   Basic input validation checks if the query is empty.
*   The user's `query_text` is sent to the ChromaDB `collection.query()` method.
*   `N_QUERY_RESULTS` (`2`) specifies that the two most semantically similar movie descriptions should be retrieved based on their vector embeddings.
*   The results, including `ids`, original `documents` text, `metadatas`, and `distances` (similarity scores), are returned.

**Step 6: Display Query Results**
*   The script iterates through the `results` obtained from the query.
*   For each matching document, it safely extracts and prints:
    *   Its `Rank` (1st, 2nd, etc.).
    *   The `Id` of the movie.
    *   The full `Description` text.
    *   `Genre`, `Certificate`, and `Year` from the `metadata` (using `.get()` to handle potentially missing keys gracefully).
    *   The `Distance` (a measure of dissimilarity, lower is better).
*   Results are formatted for clear presentation.

**Step 7: Finalization and Error Handling**
*   A `finally` block ensures that `stop_tee()` is always called to properly close the log file, even if an exception occurs.
*   Any unhandled exceptions during the entire script execution are caught by the `main()` function's `try...except` block and printed to `sys.stderr` for better error reporting.
*   A final timestamped message indicates the script's completion.
"""
import os
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
import sys
import config
from datetime import datetime
from datetime import datetime
from tee_logger import start_tee, stop_tee
from google import genai

# --- Configuration Constants ---
DB_PATH = "./local_vectordb" 
N_QUERY_RESULTS = 2
COLLEXTION_NAME = 'movies_database'
api_key = os.getenv("GEMINI_API_KEY")
MODEL_NAME =  "models/text-embedding-004"

class custom_embeddingfunction(EmbeddingFunction):
    def __init__(self) -> None:
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_EMBEDDING_MODEL")

    def __call__(self, input: Documents) -> Embeddings:
        """ core conversion engine """    
        embeddings = []
        for text in input:
            response = self.client.models.embed_content(
            model = self.model_name,
            contents= text
        )
            embeddings.append(response.embeddings[0].values)
        return embeddings
def initiate_chroma_client(path: str) ->chromadb.PersistentClient:
    """ initializes and returns chromadb persistantclient"""
    print(f"\nStep 1. Initializing chromadb client at : {path}")
    return chromadb.PersistentClient(path=path)

embedding_fn = custom_embeddingfunction()
def get_or_create_movoes_collection(client: chromadb.PersistentClient, collection_name:str) -> chromadb.Collection:
    """deletes if exists already and then creates it"""
    print(f"\nStep 2. collection create/get procedure - {collection_name}...")
    try:
        client.delete_collection(name=collection_name)
        print(f"\n{collection_name} has been cleared and will be recreated again.....")
    except KeyError: # Catch only the expected "not found" error
        print("\nCollection 'movie_descriptions' not found, proceeding to create new one.")
    except Exception as e: # Catch any other unexpected errors, log them
        print(f"\nAn unexpected error occurred while deleting collection: {e}", file=sys.stderr)
        # sys.exit(1)
        # Optionally re-raise or handle more gracefully
    collection = client.get_or_create_collection(name=collection_name, embedding_function = embedding_fn)
    total_records = collection.count()
    print(f"\nTotal records in existing movie description database are : {total_records}")
    return collection

def prepare_movie_collection() -> list[dict]:
    """contains a list of movies with complete metadata"""
    print(f"\nStep 3. preparing movies data ....")
# We pass text documents. Chroma automatically turns them into vectors under the hood!  
    return [
        # Sci-Fi / Space
        {
            "id": "id1",
            "text": "A movie about a dark knight fighting crime in Gotham city using high-tech gadgets.",
            "meta": {"genre": "action", "certificate": "U/A", "year": "2008"}        
        },
        {
            "id": "id2",
            "text": "A romantic story about two star-crossed lovers on a doomed giant cruise ship.",
            "meta": {"genre": "romance", "certificate": "U/A", "year": "1997"}        
        },
        {
            "id": "id3",
            "text": "An astronaut gets stranded on Mars and must survive using science and wit.",
            "meta": {"genre": "sci-fi", "certificate": "A", "year": "2015"}        
        },
        {
            "id": "id4",
            "text": "A crew travels through a wormhole in space to find a new home for humanity.",
            "meta": {"genre": "sci-fi", "certificate": "A", "year": "2004"}
        },
        # Tech / AI / Cyberpunk
        {
            "id": "id5",
            "text":"A software engineer discovers that reality is a simulated matrix controlled by machines.",
            "meta": {"genre": "cyberpunk", "certificate": "U/A", "year": "2017"}
        },
        {
            "id": "id6",
            "text": "A lone hacker attempts to take down a corrupt megacorporation in a neon-lit futuristic Tokyo.",
            "meta": {"genre": "cyberpunk", "certificate": "U/A", "year": "1999"}
        },
        #Historical Drana
        {
            "id": "id7",
            "text": "A biographical drama focusing on the development of the first atomic bomb during WWII.",
            "meta": {"genre": "drama", "certificate": "U", "year": "1976"}
        },
        {
            "id": "id8",
            "text": "The rise and fall of an ancient Roman emperor told through political betrayal and gladiatorial combat.",
            "meta": {"genre": "History", "certificate": "U/A", "year": "2004"}
        },
        # Mystry / Thriller
        {
            "id" : "id9",
            "text": "A detective travels to a remote island asylum to investigate the disappearance of a patient.",
            "meta": {"genre": "Mystry", "certificate": "A", "year": "2000"}
        },
        {
            "id": "id10",
            "text": "A quiet dinner party turns chaotic when a comet passes overhead, fracturing reality into parallel timelines.",
            "meta": {"genre": "thriller", "certificate": "U/A", "year": "1956"}        
        }
    ]

def add_document_to_collection(collection: chromadb.Collection, documents: list[dict]):
    """add a document to the movies collection in chromadb"""
    print(f"\nStep 4. Inserting {len(documents)} records into '{collection.name}' ...")
    collection.add(ids=[d["id"] for d in documents],
                documents= [d["text"] for d in documents],
                metadatas=[d["meta"] for d in documents]
                )
    print("\n....... Document insertion complete .......")
    total_records = collection.count()
    print(f"\nTotal records in existing movie description database '{collection.name}' are : {total_records}")

def query_collection(collection: chromadb.Collection, n_results: int):
    """prompts user to write a query and prints the top results"""
    print("\nStep 5. Querying the database..")
    query_text = input("\nwrite your query on movies: ")

    if not query_text .strip():
        print("Query cannot be empty. Please enter a valid query.", file=sys.stderr)
        return
    
    print(f"...Querying ...: {query_text} for top {n_results} results")
    results = collection.query(query_texts=[query_text], n_results=n_results)# Bring back the best 2 match

    if results and results["ids"] and results["ids"][0]:
        print("\n ------ query results ------")
        for i in range(len(results['ids'][0])):
            match_id = results['ids'][0][i]
            doc_text = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            genre = metadata.get('genre', 'N/A')# Provides 'N/A' if 'genre' key is missing
            year = metadata.get('year')
            distance = results["distances"][0][i]
            print(f"\nRank = {i +1}: Match Id: {match_id} Description: {doc_text} Genre: {genre} released in {year} Distance: {distance}")
            print("-----------------------")
    else: 
        print("\n No results fiound for your query ")

def main():
    """main function to run the chromadb functions"""
    now = datetime.now()
    tree_stream = None
    try:
        tree_stream = start_tee(__file__)
        client = initiate_chroma_client(DB_PATH)
        collection = get_or_create_movoes_collection(client, COLLEXTION_NAME)

        documents_to_add = prepare_movie_collection()
        add_document_to_collection(collection, documents_to_add)

        query_collection(collection, N_QUERY_RESULTS)
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