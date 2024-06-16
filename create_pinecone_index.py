import os
import os
from dotenv import load_dotenv
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec

load_dotenv()
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone.create_index(name=os.getenv('PINECONE_INDEX'), dimension=1536, metric="cosine",
    spec=ServerlessSpec(
        cloud='aws', 
        region='us-west-2'
    ) 
) 
