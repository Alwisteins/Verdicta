from src.graph.state import GraphState

def route_question (state: GraphState) -> str:
    """
    Membaca question_category hasil olahan router_node.
    Untuk saat ini, semua kategori yang butuh data dokumen akan diarahkan ke retrieve_node.
    """
    category = state.get("question_category", "general_inquiry")
    
    return "retrieve_node"