from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import GraphState
from src.graph.nodes import router_node, retrieve_node, generation_node
from src.graph.edges import route_question

workflow = StateGraph(GraphState)

workflow.add_node("router_node", router_node)
workflow.add_node("retrieve_node", retrieve_node)
workflow.add_node("generation_node", generation_node)

workflow.set_entry_point("router_node")

workflow.add_conditional_edges(
    "router_node",
    route_question,
    {
        "retrieve_node": "retrieve_node"
    }
)

workflow.add_edge("retrieve_node", "generation_node")
workflow.add_edge("generation_node", END)

checkpointer = MemorySaver()

app = workflow.compile(checkpointer=checkpointer)