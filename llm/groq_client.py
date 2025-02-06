# llm/groq_client.py
from langchain_groq import ChatGroq
from config import GROQ_API_KEY

def get_groq_client():
    """Initialize and return the Groq client."""
    return ChatGroq(groq_api_key=GROQ_API_KEY, model="llama3-70b-8192")