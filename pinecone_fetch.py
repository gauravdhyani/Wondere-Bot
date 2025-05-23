import pinecone
import os
from dotenv import load_dotenv
load_dotenv() 

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("wondere")

def query_similar_messages(input_text):
    embedding_response = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[input_text],
        parameters={"input_type": "query"}  
    )

    embedding = embedding_response[0].values

    res = index.query(
        vector=embedding,
        top_k=5,
        namespace="messages",
        include_metadata=True
    )

    if res.matches:
        return [match.metadata['text'] for match in res.matches]
    else:
        return []

