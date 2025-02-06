# llm/prompt_manager.py
from langchain.prompts import ChatPromptTemplate
from langchain.schema.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from config import SYSTEM_PROMPT

def generate_response(prompt, model):
    """Generate a response using the Groq model."""
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        ("human", "{prompt}"),
    ])
    chain = chat_prompt | model | StrOutputParser()
    return chain.invoke({"prompt": prompt})