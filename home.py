from llama_index.llms import OpenAI
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import streamlit as st

# Set up the Qdrant client for Business Halland
url = 'qdrant.utvecklingfalkenberg.se'
api_key = st.secrets["QDRANT_API_KEY"]
client = QdrantClient(url=url, api_key=api_key, port=443)
llm = OpenAI(temperature=0.1, model="gpt-4-1106-preview") # Use the appropriate GPT-4 model

# Create QdrantVectorStore for storing business-related data
vector_store = QdrantVectorStore(client=client, collection_name="businesshalland")

# Create the storage and service contexts for processing business queries
storage_context = StorageContext.from_defaults(vector_store=vector_store)
service_context = ServiceContext.from_defaults(llm=llm)

# Build the VectorStoreIndex for efficient data retrieval
index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context, service_context=service_context)

# Create a query engine for business-related inquiries
query_engine = index.as_query_engine(streaming=True, similarity_top_k=3)

# Streamlit UI setup for the Business Guide Bot
st.title("Hallands Företagsguide Bot 🤖")
st.caption('Välkommen till Företagsguide Bot för Halland! Jag är här för att hjälpa dig med frågor om att starta och driva företag i Halland. Fråga mig om allt från registrering, finansiering till marknadsföring och export.')

user_input = st.text_input("**Vad vill du veta om företagande i Halland?** *(Ställ din fråga på valfritt språk)*")
if user_input:
    # Stream the GPT-4 reply
    response = query_engine.query(f"System instructions: Du hjälper användare med frågor om hur företag kan få hjälp och inspiration att utveckla sitt företag inom olika områden och från olika aktörer. Inkludera länkar till relevanta källor i dina svar. Svara enkelt och tydligt, gärna i punktform där det passar. Användarens fråga: {user_input}. Inkludera alltid källhänvisningar och svara på samma språk som frågan.")
    
    with st.sidebar:
        for node in response.source_nodes:
            text = node.node.text
            score = node.score
            st.write(f"Text: {text}, Score: {score}")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        for chunk in response.response_gen:
            full_response += chunk
            message_placeholder.markdown(full_response)
