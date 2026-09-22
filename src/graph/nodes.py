from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from src.retrieval.vector import VectorStoreManager

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0
)

vector_manager = VectorStoreManager()

def retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node semantic search dengan filter metadata (nomor_uu, category, pasal) saat query relevan.
    """
    query = state.get("query") or state.get("question", "")
    filter_dict = state.get("filter_dict", {})
    k = state.get("k", 4)
    
    if not query:
        return {"documents": []}
        
    docs = vector_manager.search_documents(query=query, k=k, filter_dict=filter_dict)
    return {"documents": docs}


