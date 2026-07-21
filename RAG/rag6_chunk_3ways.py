"""
**Chunking**
Chunk one long BFSI document/paragraphs three ways.
See how chunk size and overlap affect what gets retrieved.
No vector DB yet — just chunking and inspection.
"""
from tee_logger import start_tee, stop_tee
from datetime import datetime
# Long BFSI paragraph -----------------------
DOCUMENT = """

POLICY: Non-Performing Asset Management and Restructuring Guidelines

Section 1 - Classification
Any loan account where interest or principal repayment is overdue for more 
than 90 days shall be classified as a Non-Performing Asset (NPA). 
Sub-standard assets are NPAs that have remained so for less than 12 months. 
Doubtful assets are NPAs that have remained sub-standard for more than 12 months. 
Loss assets are those where the bank has identified the loss but the amount 
has not been written off.

Section 2 - Restructuring Eligibility  
A borrower is eligible for restructuring if the account was standard for 
the preceding 12 months before being classified as NPA. 
The borrower must demonstrate viable business operations and submit 
audited financials for the last 3 years. 
Restructuring requires approval from the Credit Committee for amounts 
above INR 50 lakhs and board approval for amounts above INR 5 crores.

Section 3 - Required Documentation
The borrower must submit Form 15C duly signed by a chartered accountant. 
A detailed viability study prepared by an independent agency is mandatory 
for accounts above INR 1 crore. 
Property valuation reports must not be older than 6 months. 
All guarantors must provide fresh consent letters before restructuring is approved.

Section 4 - RBI Reporting
All restructured accounts must be reported to the Central Repository of 
Information on Large Credits (CRILC) within 30 days of restructuring. 
Accounts above INR 5 crores must be reported individually. 
Quarterly progress reports on restructured accounts must be submitted 
to the RBI Regional Office by the 15th of the following month.
""".strip()
# print(DOCUMENT)

def chunk_fixed_size(text: str, size: int, overlap: int) -> list[str]:
    """Fixed chunking with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        # print(f"End = {end}")
        chunks.append(text[start:end])
        start += size - overlap
        # print(f"Start = {start}")
    return (chunks)

def chunks_by_section(text: str) -> list[str]:
    """Split on section headers — semantic chunking."""
    import re
    sections = re.split(r'\n\n(?=Section \d+)' , text)
    return[s.strip() for s in sections if s.strip()]
    # return sections

def print_chunks(chunks: list[str], label: str):
    """Prints chukns in formatted fashion"""
    print(f"\n{'='*60}")
    print(f"{label} — {len(chunks)} chunks")
    print('='*60)
    for i, chunk in enumerate(chunks):
        print(f"\n[Chunk {i+1}] {len(chunk)} chars")
        print(chunk)#[:120] + "..." if len(chunk) > 120 else chunk)

def main():
    print(f"\n Document length is {len(DOCUMENT)} Characters")
    tee_stream = []
    now = datetime.now()
    tee_stream = start_tee(__file__)
    # Strategy 1 — small chunks, no overlap
    chunk_a = chunk_fixed_size(DOCUMENT, 200, 40)
    print_chunks(chunk_a, "Fixed 300 chars, NO overlap")
    # Strategy 2 — small chunks, with overlap
    chunk_b = chunk_fixed_size(DOCUMENT, 300, 100)
    print_chunks(chunk_b, "Fixed 300 chars, 100 characters overlap")
    # Strategy 3 — semantic split on section headers
    chunk_c = chunks_by_section(DOCUMENT)
    print_chunks(chunk_c, "By Section Chunking")
    stop_tee(tee_stream)
    print(f"\n Script Execution ends - {now}")
if __name__ == "__main__":
    main()
