import os
import uuid
from dotenv import load_dotenv

load_dotenv()

import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel # NEO: Το χρειαζόμαστε για το νέο endpoint

# Import to schema kai ton agent
from api.schemas import ChatRequest
from core.graph import app as agent_app

MEMORY_STORE = {}

app = FastAPI(title="Agentic Planner API", version="1.0.0")

# Rythmish CORS gia na mhn mplokarei o browser me thn React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ΝΕΟ: Schema για να δεχόμαστε το διορθωμένο πλάνο
class ResumeRequest(BaseModel):
    thread_id: str
    plan: list  # Λίστα με τα βήματα του πλάνου

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Δέχεται το μήνυμα του χρήστη και επιστρέφει streaming events (SSE) 
    για κάθε βήμα της εκτέλεσης (Plan -> Execution -> Final Response).
    """
    
    async def event_generator():
        thread_id = request.thread_id or "default"
        
        # NEO: Η "ταυτότητα" της μνήμης για το LangGraph
        config = {"configurable": {"thread_id": thread_id}}
        
        # 1. Δημιουργία ή φόρτωση custom μνήμης για αυτόν τον χρήστη
        if thread_id not in MEMORY_STORE:
            MEMORY_STORE[thread_id] = []
            
        # Παίρνουμε μόνο τα τελευταία 20 μηνύματα (10 exchanges) για να μην σκάσει το API
        recent_history = MEMORY_STORE[thread_id][-20:]

        initial_state = {
            "input": request.message,
            "chat_history": recent_history,  # Δίνουμε τη μνήμη στον Agent
            "plan": [],
            "current_step_index": 0,
            "final_response": ""
        }

        final_answer = ""

        try:
            # NEO: Προσθέσαμε το config=config για να ενεργοποιηθεί η Μνήμη
            async for output in agent_app.astream(initial_state, config=config):
                for node_name, state_update in output.items():

                    # Φτιάχνω ένα μοναδικό ID για αυτό το log
                    log_id = str(uuid.uuid4())
                    log_msg = f"Ενημέρωση από: {node_name.upper()}"
                    
                    if node_name == "planner":
                        log_msg = "⚙️ [PLANNER] Παραγωγή νέου πλάνου εκτέλεσης..."
                    elif node_name == "executor":
                        log_msg = "🛠️ [EXECUTOR] Εκτέλεση βημάτων και κλήση εργαλείων..."
                    elif node_name == "finalizer":
                        log_msg = "🧠 [FINALIZER] Σύνθεση τελικής απάντησης..."
                        
                    yield {
                        "event": "log",
                        "data": json.dumps({"id": log_id, "message": log_msg}, ensure_ascii=False)
                    }
                    
                    if node_name == "planner":
                        yield {
                            "event": "plan_generated",
                            "data": json.dumps({"plan": state_update["plan"]}, ensure_ascii=False)
                        }
                        
                    elif node_name == "executor":
                        yield {
                            "event": "step_executed",
                            "data": json.dumps({"plan": state_update.get("plan", [])}, ensure_ascii=False)
                        }
                        
                    elif node_name == "finalizer":
                        final_answer = state_update.get("final_response", "")
                        yield {
                            "event": "final_response",
                            "data": json.dumps({"response": final_answer}, ensure_ascii=False)
                        }
                
                await asyncio.sleep(0.1)

            # --- ΝΕΟ: Ο ΑΝΙΧΝΕΥΤΗΣ ΦΡΕΝΟΥ ---
            current_state = agent_app.get_state(config)
            
            # ΑΛΛΑΓΗ ΕΔΩ: Τώρα περιμένουμε να κολλήσει στο human_review
            if current_state.next and "human_review" in current_state.next:
                yield {
                    "event": "waiting_for_user",
                    "data": json.dumps({"plan": current_state.values.get("plan", [])}, ensure_ascii=False)
                }
                return # Κόβουμε το stream εδώ! Το γράφημα περιμένει τον χρήστη.
            # ---------------------------------

            # 2. Αφού τελειώσει επιτυχώς, αποθηκεύουμε την ανταλλαγή στη Μνήμη
            if final_answer:
                MEMORY_STORE[thread_id].append({"role": "User", "content": request.message})
                MEMORY_STORE[thread_id].append({"role": "Agent", "content": final_answer})

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"detail": str(e)}, ensure_ascii=False)
            }

    return EventSourceResponse(event_generator())


# --- ΝΕΟ ENDPOINT: Η ΣΥΝΕΧΕΙΑ (RESUME) ---
@app.post("/chat/resume")
async def chat_resume(request: ResumeRequest):
    async def resume_generator():
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # 1. Αλλάζουμε τη μνήμη "αθόρυβα" (χωρίς as_node)
        agent_app.update_state(
            config, 
            {"plan": request.plan, "current_step_index": 0}
        )
        
        final_answer = ""
        try:
            # 2. ΤΟ ΜΥΣΤΙΚΟ: Περνάμε None! Αυτό σημαίνει "Ξεπάγωσε και συνέχισε!"
            async for output in agent_app.astream(None, config=config):
                for node_name, state_update in output.items():
                    log_id = str(uuid.uuid4())
                    
                    print(f"DEBUG: Resuming node -> {node_name}")
                    
                    log_msg = f"Ενημέρωση από: {node_name.upper()}"
                    if node_name == "executor":
                        log_msg = "🛠️ [EXECUTOR] Εκτέλεση διορθωμένου πλάνου..."
                    elif node_name == "finalizer":
                        log_msg = "🧠 [FINALIZER] Σύνθεση τελικής απάντησης..."
                        
                    yield {
                        "event": "log",
                        "data": json.dumps({"id": log_id, "message": log_msg}, ensure_ascii=False)
                    }

                    if node_name == "executor":
                        current_plan = agent_app.get_state(config).values.get("plan", [])
                        yield {
                            "event": "step_executed",
                            "data": json.dumps({"plan": current_plan}, ensure_ascii=False)
                        }
                        
                    elif node_name == "finalizer":
                        final_answer = state_update.get("final_response", "")
                        yield {
                            "event": "final_response",
                            "data": json.dumps({"response": final_answer}, ensure_ascii=False)
                        }
                
                await asyncio.sleep(0.1)

            if final_answer:
                MEMORY_STORE.setdefault(request.thread_id, []).append({"role": "Agent", "content": final_answer})

        except Exception as e:
            print(f"RESUME ERROR: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"detail": str(e)}, ensure_ascii=False)
            }

    return EventSourceResponse(resume_generator())
# ----------------------------------------

# Elegxo an o server einai zontanos
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Agentic Planner Backend is running!"}