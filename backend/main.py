import os
import uuid
from dotenv import load_dotenv

load_dotenv()

import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse



# Import to schema kai ton agent
from api.schemas import ChatRequest
from core.graph import app as agent_app

MEMORY_STORE = {}

app = FastAPI(title="Agentic Planner API", version="1.0.0")


# Rythmish CORS gia na mhn mplokarei o browser me thn React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Edo tha mpei to URL ths React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Δέχεται το μήνυμα του χρήστη και επιστρέφει streaming events (SSE) 
    για κάθε βήμα της εκτέλεσης (Plan -> Execution -> Final Response).
    """
    
    async def event_generator():
        thread_id = request.thread_id or "default"
        
        # 1. Δημιουργία ή φόρτωση μνήμης για αυτόν τον χρήστη
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
            async for output in agent_app.astream(initial_state):
                for node_name, state_update in output.items():

                    # Φτιάχνω ένα μοναδικό ID για αυτό το log
                    log_id = str(uuid.uuid4())
                    # Στέλνουμε το log ανάλογα με τον κόμβο
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
                            "data": json.dumps({"plan": state_update["plan"]}, ensure_ascii=False)
                        }
                        
                    elif node_name == "finalizer":
                        final_answer = state_update["final_response"]
                        yield {
                            "event": "final_response",
                            "data": json.dumps({"response": final_answer}, ensure_ascii=False)
                        }
                
                await asyncio.sleep(0.1)

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

# Elegxo an o server einai zontanos
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Agentic Planner Backend is running!"}