""" this is example to uderstand embeddings and cosine similarity"""
""" Script writer : claude """

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tee_logger import start_tee, stop_tee
from datetime import datetime
import numpy as np

tee = start_tee(__file__)
now = datetime.now()
formatted_string = now.strftime("Execution ends - %Y-%m-%d - %H:%M:%S")

model = SentenceTransformer('all-MiniLm-L6-V2')

sentences = [
    "What is the policy for loan restructuring of NPA accounts?",
    "Guidelines for restructuring non-performing assets and debt workouts.",
    "The quarterly cricket tournament starts next Monday."
]

embeddings = model.encode(sentences)
print(f"Embedding Shapes : {embeddings.shape}")
print(f"Each Vector has : {embeddings.shape[1]} dimensions\n")

# printing first 8 numbers of each vector 
for i, sentence in enumerate(sentences):
    preview = ", ".join(f"{x:.3f}" for x in embeddings[i][:8])
    print (f"Sentence : { i + 1} : [{preview}.....]")

# Now computing similarity between all pairds
print("\nSimilarity Scores ...........\n")
pairs = [(0,1), (0,2), (1,2)]
labels = [
    "NPA Query vs NPA Guidelines",
    "NPA Query vs Cricket",
    "NPA Guidelines vs Cricket"
]

for (i, j), label in zip(pairs, labels):
    score = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
    print(f"{label}: {score:.4f}")

print(formatted_string)
stop_tee(tee)
