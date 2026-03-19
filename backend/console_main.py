import os
from dotenv import load_dotenv


load_dotenv()


from core.graph import app

def main():
    print("Ξεκινάει ο Agentic Planner \n")
    
    while True:
        user_input = input("\nΕσύ: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Arxiko state
        initial_state = {
            "input": user_input,
            "plan": [],
            "current_step_index": 0,
            "final_response": ""
        }
        
        # Trexo graph
        print("\n--- Agent Execution ---")
        final_state = app.invoke(initial_state)
        
        print("\n--- Τελικό Πλάνο που εκτελέστηκε ---")
        for step in final_state["plan"]:
            print(f"[{step['status'].upper()}] Βήμα {step['step_id']}: {step['description']} (Tool: {step['tool']})")
        
        print("\nAgent:", final_state["final_response"])

if __name__ == "__main__":
    main()