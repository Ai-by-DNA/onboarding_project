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
    tool: str = Field(description="Το όνομα του εργαλείου: 'web_search', 'calculator', ή 'file_reader'")

class PlanOutput(BaseModel):
    steps: List[Step]

# Graph Nodes

def planner_node(state: AgentState) -> dict:

    print("[Planner] Γράφω το πλάνο...")
    
    system_prompt = """Είσαι ένας έξυπνος Planner Agent. 
    Σπάσε το αίτημα του χρήστη σε λογικά βήματα. 
    Διαθέσιμα εργαλεία: 'web_search', 'calculator', 'file_reader'.
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

    plan = state["plan"]
    index = state["current_step_index"]
    
    current_step = plan[index]
    tool_name = current_step["tool"]
    description = current_step["description"]
    
    print(f"[Executor] Εκτέλεση Βήματος {current_step['step_id']}: {description} (Tool: {tool_name})")
    
    current_step["status"] = "in_progress"
    
    # Lathos ergaleio
    if tool_name not in TOOLS_MAP:
        current_step["status"] = "failed"
        current_step["result"] = f"Tool {tool_name} not found."
    else:
        # Xrhsimopoio to LLM gia na ftiaxei to sosto input gia to ergaleio
        tool_prompt = f"""Πρέπει να εκτελέσεις αυτό το βήμα: '{description}'.
        Το αρχικό ερώτημα ήταν: '{state['input']}'.
        Ποιο πρέπει να είναι το input string για το εργαλείο {tool_name}; 
        Επίστρεψε ΜΟΝΟ το input string, τίποτα άλλο."""
        
        tool_input = llm.invoke(tool_prompt).content.strip()
        
        # Kalo to ergaleio
        tool_function = TOOLS_MAP[tool_name]
        result = tool_function.invoke(tool_input)
        
        current_step["status"] = "completed"
        current_step["result"] = result
        print(f"   ↳ Αποτέλεσμα: {result[:100]}...") # protoi 100 xarakthres
    
    # next step
    plan[index] = current_step
    return {"plan": plan, "current_step_index": index + 1}


def finalizer_node(state: AgentState) -> dict:

    print("[Finalizer] Συνθέτω την τελική απάντηση...")
    
    summary_prompt = f"""Το αρχικό ερώτημα ήταν: '{state['input']}'.
    Εδώ είναι τα βήματα που εκτελέστηκαν και τα αποτελέσματά τους:
    {state['plan']}
    
    Γράψε την τελική, φιλική και χρήσιμη απάντηση για τον χρήστη."""
    
    final_response = llm.invoke(summary_prompt).content
    return {"final_response": final_response}