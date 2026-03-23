from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    input: str #oti dosei o xrhsths
    chat_history: list[dict] 
    plan: List[Dict[str, Any]] #to plano
    current_step_index: int
    final_response: str #apanthsh ston xrhsth