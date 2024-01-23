import json
from llama_index import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.llms import OpenAI
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import streamlit as st
from llama_index import Document

def load_content_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    urls = [item.get("url", "") for item in json_data]
    texts = [item.get("texts", "") for item in json_data]
    return urls, texts

json_file_path = 'data/scraped_data2.json'
url_list, text_list = load_content_from_json(json_file_path)

# Set up the Qdrant client
url = 'qdrant.utvecklingfalkenberg.se'
api_key = st.secrets["QDRANT_API_KEY"]
client = QdrantClient(url=url, api_key=api_key, port=443)
OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']

# Load documents
documents = []
for url, text in zip(url_list, text_list):
    if text:  # Only create documents for non-empty texts
        doc = Document(text=text, metadata={"url": url})
        documents.append(doc)

# Create QdrantVectorStore
vector_store = QdrantVectorStore(client=client, collection_name="businesshalland")

# Create the storage and service contexts
llm = OpenAI(temperature=0.0, model='gpt-4-1106-preview')
storage_context = StorageContext.from_defaults(vector_store=vector_store)
service_context = ServiceContext.from_defaults(llm=llm)

# Build the VectorStoreIndex
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, service_context=service_context)
