from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from core.state import AgentState
from core.tools import TOOLS_MAP

# Setup του LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Pydantic
class Step(BaseModel):
    step_id: int
    description: str = Field(description="Τι ακριβώς πρέπει να γίνει σε αυτό το βήμα")
    tool: str = Field(description="Το όνομα του εργαλείου: 'web_search', 'calculator', ή 'file_reader', ή 'none' αν δεν απαιτείται κάποιο εργαλείο")

class PlanOutput(BaseModel):
    steps: List[Step]

# Graph Nodes

def planner_node(state: AgentState) -> dict:
    """Δημιουργεί το αρχικό πλάνο."""
    print("\n [Planner] Γράφω το πλάνο...")
    
    system_prompt = """Είσαι ένας έξυπνος Planner Agent. 
    Σπάσε το αίτημα του χρήστη σε λογικά βήματα. 
    Διαθέσιμα εργαλεία: 'web_search', 'calculator', 'file_reader'.
    Αν ένα βήμα δεν χρειάζεται εργαλείο (π.χ. απλή σύνθεση πληροφοριών), βάλε tool='none'.
    Επίστρεψε ΜΟΝΟ το δομημένο πλάνο."""
    
    # Epistrefei JSON
    structured_llm = llm.with_structured_output(PlanOutput)
    
    plan_result = structured_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["input"]}
    ])
    
    # Metatrepo ta Pydantic objects se leksika
    plan_dicts = []
    for step in plan_result.steps:
        plan_dicts.append({
            "step_id": step.step_id,
            "description": step.description,
            "tool": step.tool,
            "status": "pending",
            "result": None
        })
        
    return {"plan": plan_dicts, "current_step_index": 0}


def executor_node(state: AgentState) -> dict:
    """Εκτελεί το τρέχον βήμα του πλάνου με Retry Logic."""
    plan = state["plan"]
    index = state["current_step_index"]
    
    current_step = plan[index]
    tool_name = current_step["tool"]
    description = current_step["description"]
    
    print(f"\n [Executor] Εκτέλεση Βήματος {current_step['step_id']}: {description} (Tool: {tool_name})")
    
    current_step["status"] = "in_progress"
    
    # Den xreiazete ergaleio
    if tool_name == "none":
        current_step["status"] = "completed"
        current_step["result"] = "Δεν απαιτήθηκε εργαλείο. Σύνθεση δεδομένων από τον Finalizer."
        print("   ↳ Αποτέλεσμα: Το βήμα θα ολοκληρωθεί μέσω εσωτερικής γνώσης/σύνθεσης.")
        plan[index] = current_step
        return {"plan": plan, "current_step_index": index + 1}

    # Den yparxei to ergaleio
    if tool_name not in TOOLS_MAP:
        current_step["status"] = "failed"
        current_step["result"] = f"Tool '{tool_name}' not found."
        plan[index] = current_step
        return {"plan": plan, "current_step_index": index + 1}

    # Ektelesh ergaleiou me max 2 retries
    tool_function = TOOLS_MAP[tool_name]
    max_retries = 2
    attempts = 0
    success = False
    final_result = ""
    
    tool_prompt = f"""Πρέπει να εκτελέσεις αυτό το βήμα: '{description}'.
    Το αρχικό ερώτημα ήταν: '{state['input']}'.
    Ποιο πρέπει να είναι το input string για το εργαλείο {tool_name}; 
    Επίστρεψε ΜΟΝΟ το input string, τίποτα άλλο."""

    while attempts <= max_retries and not success:

        tool_input = llm.invoke(tool_prompt).content.strip()
        

        final_result = tool_function.invoke(tool_input)
        
        # Elegxo an to apotelesma einai error
        if not str(final_result).startswith("Error"):
            success = True
            current_step["status"] = "completed"
        else:
            attempts += 1
            if attempts <= max_retries:
                print(f"   Σφάλμα ('{final_result}'). Προσπάθεια {attempts}/{max_retries}...")
                # Enhmerono to LLM gia to ti phge lathos
                tool_prompt += f"\n\nΠΡΟΣΟΧΗ: Η προηγούμενη προσπάθεια απέτυχε με αυτό το σφάλμα: {final_result}. Δώσε ένα ΔΙΑΦΟΡΕΤΙΚΟ ή διορθωμένο input."
    
    if not success:
        current_step["status"] = "failed"
        print("   Το βήμα απέτυχε οριστικά μετά από 3 προσπάθειες (1 αρχική + 2 retries).")
    
    current_step["result"] = final_result
    # Protes 150 lekseis apo to apotelesma
    print(f"   ↳ Αποτέλεσμα: {str(final_result)[:150]}...") 
    
    plan[index] = current_step
    return {"plan": plan, "current_step_index": index + 1}
    



def finalizer_node(state: AgentState) -> dict:
    """Συνθέτει την τελική απάντηση με βάση τα αποτελέσματα."""
    print("[Finalizer] Συνθέτω την τελική απάντηση...")
    
    summary_prompt = f"""Το αρχικό ερώτημα ήταν: '{state['input']}'.
    Εδώ είναι τα βήματα που εκτελέστηκαν και τα αποτελέσματά τους:
    {state['plan']}
    
    Γράψε την τελική, φιλική και χρήσιμη απάντηση για τον χρήστη."""
    
    final_response = llm.invoke(summary_prompt).content
    return {"final_response": final_response}