from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.agents import planner_node, executor_node, finalizer_node

def router(state: AgentState) -> str:
   
    # Apofasizei pou tha paei to graph meta ton executor
    plan = state["plan"]
    index = state["current_step_index"]
    
    # An oxi alla vhmata phgene sto telos
    if index >= len(plan):
        return "finalizer"
    # Allios synexise
    return "executor"


workflow = StateGraph(AgentState)


workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("finalizer", finalizer_node)

# Roh me velakia
workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")

# Ο executor paei ston router gia na dei an prepei na kanei loop
workflow.add_conditional_edges(
    "executor",
    router,
    {
        "executor": "executor",     # Loop back
        "finalizer": "finalizer"    # Break loop
    }
)

workflow.add_edge("finalizer", END)

# Compile agent
app = workflow.compile()