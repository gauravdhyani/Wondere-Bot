import os
import time
import pandas as pd
import re
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec

# === CONFIG ===
PINECONE_API_KEY = "Your pinecone key" #Enter your key
INDEX_NAME = "Your Inded name" #Name of your index
CSV_PATH = r'.\user_messages.csv' #Path to extracted messages
MAX_CHARS = 7000  # Safe limit for ~2048 tokens

# === INIT ===
pc = Pinecone(api_key=PINECONE_API_KEY)

# Ensure index exists
if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1") #Edit cloud and region accordingly
    )

index = pc.Index(INDEX_NAME)

# === CLEANING FUNCTION ===
def clean_message(msg, max_chars=MAX_CHARS):
    if not isinstance(msg, str):
        return None
    msg = msg.strip()
    if not msg or len(msg) > max_chars:
        return None
    msg = re.sub(r"[!?.,]{3,}", ".", msg)              # Normalize punctuation
    msg = re.sub(r"(.)\1{3,}", r"\1", msg)              # Normalize repeated chars
 
    return msg

# === LOAD & CLEAN MESSAGES ===
df = pd.read_csv(CSV_PATH)
messages = df['Content'].dropna().tolist()
clean_messages = [clean_message(m) for m in messages]
clean_messages = [m for m in clean_messages if m]
print(f"{len(clean_messages)} clean messages ready for embedding.")

# === EMBED & UPSERT ===
batch_size = 48  # safer size

for i in tqdm(range(0, len(clean_messages), batch_size)):
    batch_texts = clean_messages[i:i + batch_size]

    try:
        response = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=batch_texts,
            parameters={"input_type": "passage"}
        )
        embeddings = response.get('data', response)  # handle both formats
    except Exception as e:
        print(f"Embedding failed at batch {i}: {e}")
        continue

    to_upsert = []
    for j, item in enumerate(embeddings):
        vector_values = item.get('values') or item.get('embedding')
        if vector_values:
            to_upsert.append({
                "id": f"msg-{i + j}",
                "values": vector_values,
                "metadata": {"text": batch_texts[j]}
            })

    try:
        index.upsert(vectors=to_upsert, namespace="messages")
    except Exception as err:
        print(f"Upsert failed at batch starting {i}: {err}")

    time.sleep(0.5)


print("All messages embedded and uploaded.")
