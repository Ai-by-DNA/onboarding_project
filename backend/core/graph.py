from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.agents import planner_node, executor_node, finalizer_node
from langgraph.checkpoint.memory import MemorySaver

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

# Φτιάχνουμε έναν άδειο κόμβο που δεν κάνει τίποτα
def human_review_node(state: AgentState):
    return state
workflow.add_node("human_review", human_review_node)

# --- Η ΝΕΑ ΡΟΗ ---
workflow.set_entry_point("planner")
workflow.add_edge("planner", "human_review") # Ο Planner πάει στον Έλεγχο
workflow.add_edge("human_review", "executor") # Ο Έλεγχος πάει στον Executor

# Ο executor paei ston router gia na dei an prepei na kanei loop
workflow.add_conditional_edges(
    "executor",
    router,
    {
        "executor": "executor",
        "finalizer": "finalizer"
    }
)

workflow.add_edge("finalizer", END)

memory = MemorySaver()

# Βάζουμε το φρένο ΜΟΝΟ στον σταθμό ελέγχου
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review"] 
)

