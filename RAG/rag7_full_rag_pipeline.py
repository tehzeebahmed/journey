"""
Document → Chunk → Embed → Store in ChromaDB
                                    ↓
User Question → Embed → Search ChromaDB → Top chunks
                                    ↓
          chunks + question → Mistral → Final Answer
✅ User question
✅ Retrieved chunks (the relevant policy text)
✅ Inject context
✅ Final answer

The "Augmented Generation" part of RAG:
Retrieval  → find relevant chunks from ChromaDB
Augmented  → inject those chunks into the prompt as context
Generation → LLM generates answer using that context
          
 Full RAG Pipeline
BFSI policy assistant — chunk, embed, store, retrieve, answer.         
          """
import os
import sys
import chromadb
import config
from llm_router import chat
from google import genai
from pathlib import Path
from datetime import datetime
from tee_logger import start_tee, stop_tee
from sentence_transformers import SentenceTransformer
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings


MODEL = 'all-MiniLM-L6-v2'
embedder = SentenceTransformer(MODEL)
N_QUERY_RESULTS = 4
DB_PATH = "./local_vectordb"
COLLECTION_NAME = "BFSIPolicyDocument"
NPA_POLICY = 'bfsi_policy_document.txt'
CURR_path = Path(__file__).parent
print(f"{CURR_path}")
POLICY_PATH = CURR_path.joinpath(NPA_POLICY)
print(f"\n {POLICY_PATH}")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")


class custom_embeddingfunction(EmbeddingFunction):
    def __init__(self) -> None:
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_EMBEDDING_MODEL")
        if not self.model_name:
                    raise ValueError("GEMINI_EMBEDDING_MODEL environment variable not set for custom_embeddingfunction.")

    def __call__(self, input: Documents) -> Embeddings:
        """ Core conversion engine with potential batching """
        # Check if input is empty
        if not input:
            return []
           
        embeddings = []
        for text in input:
            response = self.client.models.embed_content(
            model = self.model_name,
            contents= text
        )
            embeddings.append(response.embeddings[0].values)
        return embeddings
def initiate_chroma_instance(path: str)-> chromadb.PersistentClient:
    "initiating chromadb instance"
    print("Step 1- Initiating Chromadb instance....")
    return chromadb.PersistentClient(path=path)

# def embed(texts: list[str]) -> list:
#     return embedder.encode(texts).tolist()

def chunk_fixed_size(text: str, size: int, overlap: int) -> list[str]:
    """Fixed chunking with overlap"""
    # size=300 means 300 words per chunk — much better for BFSI documents
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        # print(f"End = {end}")
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += size - overlap
        # print(f"Start = {start}")
    return (chunks)

EMBEDDING_FUNCTION_GEMINI = custom_embeddingfunction()    
def build_knowledge_base(client: chromadb.Client, text_content: str, embedding_func: EmbeddingFunction)-> chromadb.Collection:
    """create collection and index """
    # embedding_fn = custom_embeddingfunction()  # your Gemini embedding class
    # global embedding_fn # Declare intent to use global variable

    collection = client.get_or_create_collection(name = COLLECTION_NAME, 
                                     metadata = {"hnsw:space": "cosine"}, # use cosine similarity
                                     embedding_function = EMBEDDING_FUNCTION_GEMINI)  # ChromaDB calls this automatically
    if collection.count() == 0:
        chunks = chunk_fixed_size(text_content, 300, 100)
        print(f"[RAG] Indexing {len(chunks)} chunks...")

        for i , chunk in enumerate(chunks):
            collection.add(
            ids = [f"chunks_{i}"],         # Unique ID for each individual chunk 
            #embeddings = [embed(chunks)], # since I am using custom_embedding now no need for this
            documents = [chunk]            # Each document is a single string chunk
            )
        print(f"[RAG] Knowledge base ready — {collection.count()} chunks indexed")
    else:
            print(f"[RAG] Collection already has {collection.count()} chunks — skipping index")
    return collection
    
def query_knowledge_base(collection: chromadb.Collection, question: str, top_k: int):
    """search thru the database with the user question"""
    print(f"\nStep 4 - Querying the collection based on user question: ")
    # question  = input(" Please write your BFSI policy related question:")
    print(f"...Querying ...: {question} for top {top_k} results")
    results = collection.query(
        query_texts=[question], n_results = top_k
        )
    return results

def build_prompt_ask_llm(question: str, context_chunks: list[str]) -> str:
    """user question sent to llm"""
    context = "\n\n".join(context_chunks)
    messages = [
        {"role": "system", "content": "Answer questions using only the provided context. If the answer is not in the context say so."},
        {"role": "user", "content": f"context:\n{context}\n\nQuestion: {question}"}
    ]
    return chat(messages)    
    
     
def main():
    tee_stream = []
    start_time = datetime.now() # Capture start time
    print(f"Script Execution started - {start_time}")
    tee_stream = start_tee(__file__)
    # bfsi_policy =[]
    with open (POLICY_PATH, "r") as file:
        bfsi_policy = file.read()
        embedding_function_instance = custom_embeddingfunction()
        client = initiate_chroma_instance(DB_PATH)
        collection = build_knowledge_base(client, bfsi_policy, embedding_function_instance)

        question = input("\n\nWhat is your BFSI policy related query: ")

        results = query_knowledge_base(collection, question, top_k=N_QUERY_RESULTS)
        chunks = results['documents'][0]
        response = build_prompt_ask_llm(question, chunks)
        print(f"The reponse of the user query is: \n\n\n {response}")
    end_time = datetime.now() # Capture end time
    print(f"Script Execution ended - {end_time}")
    print(f"Total execution time: {end_time - start_time}")
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()


# Flow of the Script

# Here's the step-by-step execution flow of the `main` function after the initial setup and global definitions:

# 1.  **`main()` Function Entry:**
#     *   Records the script start time (`now`).
#     *   Initializes `tee_logger` to capture console output to a log file.

# 2.  **Load Policy Document:**
#     *   Opens the `bfsi_policy_document.txt` file (located relative to the script's directory).
#     *   Reads the entire content of the file into the `bfsi_policy` string variable.

# 3.  **Initialize ChromaDB Client:**
#     *   Calls `initiate_chroma_instance(DB_PATH)` to create or connect to a persistent ChromaDB client instance at `./local_vectordb`.
#     *   Prints "Step 1- Initiating Chromadb instance....".

# 4.  **Build Knowledge Base (ChromaDB Collection):**
#     *   Calls `build_knowledge_base(client, bfsi_policy)`.
#     *   **Inside `build_knowledge_base`:**
#         *   (Potentially re-instantiates `custom_embeddingfunction` if not corrected.)
#         *   Gets or creates a ChromaDB collection named `BFSIPolicyDocument` with `cosine` similarity and the specified `custom_embeddingfunction`.
#         *   **Checks if Collection is Empty:**
#             *   If `collection.count() == 0` (first run or empty DB):
#                 *   Calls `chunk_fixed_size(bfsi_policy, 300, 100)` to break the policy document into chunks of 300 words with 100 words overlap.
#                 *   Prints the number of chunks being indexed.
#                 *   **Iterates through each `chunk`:**
#                     *   (Attempts to) add each `chunk` to the ChromaDB collection using `collection.add()`. (This is where the logical error of adding `[chunks]` instead of `[chunk]` occurs and needs correction). ChromaDB's `embedding_function` (our `custom_embeddingfunction`) is implicitly called to embed the document(s).
#                 *   Prints confirmation that the knowledge base is ready with the count of indexed chunks.
#             *   If `collection.count() > 0`:
#                 *   Prints that the collection already has chunks and skips indexing.
#     *   Returns the `collection` object.

# 5.  **Get User Query:**
#     *   Prompts the user with `input("what is your BFSI policy related query: ")`.
#     *   Stores the user's input in the `question` variable.

# 6.  **Query Knowledge Base:**
#     *   Calls `query_knowledge_base(collection, question, top_k=N_QUERY_RESULTS)`.
#     *   **Inside `query_knowledge_base`:**
#         *   Prints "Step 4 - Querying the collection based on user question: ".
#         *   Performs a similarity search on the ChromaDB `collection` using the `question`. The `custom_embeddingfunction` is implicitly used to embed the `question`.
#         *   Retrieves the top `N_QUERY_RESULTS` (4) relevant chunks.
#     *   Returns the `results` dictionary from ChromaDB.

# 7.  **Extract Context Chunks:**
#     *   Extracts the document contents (the retrieved chunks) from `results['documents'][0]`.

# 8.  **Build Prompt and Ask LLM:**
#     *   Calls `build_prompt_ask_llm(question, chunks)`.
#     *   **Inside `build_prompt_ask_llm`:**
#         *   Combines the `context_chunks` into a single `context` string.
#         *   Constructs a list of messages for the LLM, including a system prompt to answer only from context and the user's question with the injected context.
#         *   Calls `chat(messages)` (from `llm_router`) to send the prompt to the LLM (Mistral/Gemini).
#     *   Returns the LLM's `response`.

# 9.  **Display Final Answer:**
#     *   Prints the LLM's `response` to the console.

# 10. **`main()` Function Exit:**
#     *   Stops `tee_logger`, closing the log file.
#     *   Prints the script end time (`now`, which is the start time if not corrected).
#     *   The script concludes.