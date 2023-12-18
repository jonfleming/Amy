import os
import pinecone
from dotenv import load_dotenv

load_dotenv()
pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENVIRONMENT')) 

index = pinecone.create_index('history', dimension=1536)