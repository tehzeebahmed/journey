"""
this script is used in neo4j_clcl_regu_rag.py to embed three pdf
- Protocol synopsis nn diabetes 001.pdf - Evaluate the safety of treatment, efficacy in adult subjects with type 2 diabetes 
- Dsmb charter nn diabetes 001.pdf - This charter defines responsibilities, composition and decision making procedures
- Sop dm 014 data completeness.pdf - definmes datacompleteness targets that must met prior to copilot access it
"""

import os
import config
from google import genai
import psycopg2
import pdfplumber
from pathlib import Path
from postgreSQLConnection import DatabaseConnection

GEMINI_APIKEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL")

CURR_PATH = Path(__file__).parent
PDF_FILES = [CURR_PATH.joinpath("Protocol_Synopsis_NN-DIABETES-001.pdf"), CURR_PATH.joinpath("DSMB_Charter_NN-DIABETES-001.pdf"), CURR_PATH.joinpath("SOP-DM-014_Data_Completeness.pdf")]

DB = {
    "host": os.getenv("PGHOST"), "port": "5432", "dbname": os.getenv("PGDATABASE"), "user": os.getenv("PGUSER"),"password": os.getenv("PGPASSWORD")
}
        
client = genai.Client()
# print(PDF_FILES)


    # Reading PDF Files 
def extract_text_from_pdf(pdf_str: str) -> str:
    text = ""
        # print(text)
    return text

def main():
    """to test out postgreSQL"""
    print("1")
    try:
        conn = psycopg2.connect(**DB)
        conn_curr = conn.cursor()
        print(f"PostGreSQL Conenction Successfull - {conn_curr}")
    except Exception as e:
        print(f"Errors at connection check it buy - {e}")

    chunk_size = 1000
    for file_path in PDF_FILES:
        if not file_path.exists():
            print(f"Skipping missing file - {file_path}")
            continue
        print(f"Processing - {file_path}")

        # Read file page by page to capture accurate page numbers
        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start = 1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    continue

        # Split page text into specific character length chunks
        chunks = [page_text[idx : idx + chunk_size] for idx in range(0, len(page_text), chunk_size)]
        for chunks in chunks:
            try:
                response =  client.models.embed_content(model=GEMINI_EMBED_MODEL, contents=chunks)
                embedding = response.embeddings[0].values
            # Insert into PostGreSQL
                query = """
                                INSERT INTO document_chunks 
                                (document_name, study_id, page_number, chunk_text, embedding)
                                VALUES (%s, %s, %s, %s, %s::public.vector);
                            """
                conn_curr.execute(query, 
                                (file_path.name, 'NN-DIABETES-001', page_idx, chunks, embedding)
                                )
            except Exception as embedding_error:
                print(f"Failed processing chunk in {file_path.name} (Page {page_idx}): {embedding_error}")
    try:
        conn.commit()
        conn_curr.close()
        conn.close()
        print("\nSuccessfully processed, committed, and saved all document embeddings!")
    except Exception as final_error:
        print(f"Error finalizing connection commits: {final_error}")


if __name__ == "__main__":
    main()