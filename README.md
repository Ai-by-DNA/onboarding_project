# 🧠 Plan & Act Agent – Intern Project (Implementation)

**Developer:** Christos Moutselos (AI By DNA)  
**Tech Stack:** React (Vite), FastAPI, LangGraph, LangChain  
**Status:** MVP + Streaming + HITL + Cloud Deployment 🚀  

---

## 📌 Project Overview

Αυτό το repository περιέχει την πλήρη υλοποίηση του **Plan & Act Agent**. Πρόκειται για ένα προηγμένο, Full-Stack agentic σύστημα που αναλύει πολύπλοκα αιτήματα, σχεδιάζει βήματα, επιτρέπει την **παρέμβαση του χρήστη (Human-in-the-loop)**, και εκτελεί το τελικό πλάνο χρησιμοποιώντας εξωτερικά εργαλεία, ενημερώνοντας το UI σε πραγματικό χρόνο.

---

## 🚀 Live Deployment
Το Backend του project είναι επιτυχώς deployed στο cloud μέσω **Railway**.
- **API Base URL:** `reasonable-nurturing-production.up.railway.app`

---

## 🎯 Core Capabilities Implemented

### ✅ 1. Plan Creation & Visibility
- Ο **Planner Agent** αναλύει το ερώτημα και επιστρέφει ένα αυστηρό JSON πλάνο.
- Το πλάνο εμφανίζεται στο Frontend **πριν** και **κατά τη διάρκεια** της εκτέλεσης.

### ✅ 2. Human-in-the-Loop (HITL) & Manual Overrides 🌟
- Το σύστημα "παγώνει" την εκτέλεση μετά τη δημιουργία του πλάνου.
- Ο χρήστης μπορεί να επεξεργαστεί **χειροκίνητα** τα βήματα του πλάνου (μέσω dynamic auto-resizing input fields στο UI).
- Με την έγκριση του χρήστη (Approve), ο Agent "ξεπαγώνει" και συνεχίζει την εκτέλεση με το **διορθωμένο πλάνο**.

### ✅ 3. Dynamic Execution & Tool Usage
- Ο **Executor Agent** αναλαμβάνει να "τρέξει" το πλάνο βήμα-βήμα.
- Επιλέγει αυτόματα το σωστό εργαλείο για το κάθε βήμα.
- **Error Handling:** Έχει ενσωματωμένο σύστημα **Max 2 Retries** σε περίπτωση που ένα εργαλείο αποτύχει.

### ✅ 4. Real-Time Streaming (SSE)
- Μηδενικός χρόνος αναμονής (White screen).
- Το backend χρησιμοποιεί **Server-Sent Events (SSE)** για να στέλνει ζωντανά updates στη React (Δημιουργία πλάνου -> Αναμονή για έγκριση -> Σε εξέλιξη -> Ολοκλήρωση -> Τελική απάντηση).
- Υποστήριξη διπλών endpoints (`/chat/stream` για νέα αιτήματα και `/chat/resume` για συνέχιση μετά από HITL).

### ✅ 5. Conversation Memory (Checkpointers)
- Ενσωμάτωση `MemorySaver` στο LangGraph για τη διατήρηση του Graph State (Μνήμης) ανάμεσα στα streams και τα user interrupts, επιτρέποντας συνεκτικό context (Thread IDs).

---

## 🎨 Advanced UI/UX Features

Το Frontend αναβαθμίστηκε για να προσφέρει μια premium, σύγχρονη εμπειρία χρήστη:
- **Modern Dark Theme:** Σχεδιασμός με έμφαση στο contrast, χρησιμοποιώντας Space Grey / Zinc αποχρώσεις και Glassmorphism (blur effects) στο Header και τα Inputs.
- **Empty State Animations:** Animated "Welcome Screen" με το λογότυπο που εξαφανίζεται (fade-out & slide-up) μόλις ξεκινήσει το πρώτο interaction.
- **Auto-resizing Textareas:** Τα πεδία επεξεργασίας του πλάνου προσαρμόζουν αυτόματα το ύψος τους ανάλογα με το κείμενο (χωρίς manual dragging).
- **Execution Dashboard:** Κρυφό Developer Terminal UI για παρακολούθηση των Backend Logs σε πραγματικό χρόνο μέσα από τη React.

---

## 🧰 Tools System

Το σύστημα υποστηρίζει επεκτάσιμα εργαλεία. Αυτή τη στιγμή είναι ενσωματωμένα τα εξής:

- 🌐 **web_search:** Για real-time αναζήτηση στο ίντερνετ (μέσω DuckDuckGo).
- 🧮 **calculator:** Για μαθηματικούς υπολογισμούς.
- 📄 **file_reader:** Για ανάγνωση τοπικών αρχείων κειμένου.
- 🧠 **none:** Ειδικό fallback για βήματα που απαιτούν απλή λογική (π.χ. σύνταξη κειμένου), αποτρέποντας τα LLM hallucinations.

---

## 🧠 Architecture (Multi-Agent Pattern)

Το Backend είναι χτισμένο πάνω στο **LangGraph** και ακολουθεί αρχιτεκτονική πολλαπλών κόμβων (Nodes) με state management:

1. **Planner Node:** Παράγει το JSON Plan.
2. **Human Review Node (Dummy):** Σημείο ελέγχου όπου το γράφημα κάνει `interrupt_before` περιμένοντας το API call έγκρισης από τον χρήστη.
3. **Executor Node:** Καλεί τα Tools σε βρόχο (loop) μέχρι να ολοκληρωθούν όλα τα βήματα.
4. **Finalizer Node:** Συνθέτει το τελικό Markdown κείμενο βασισμένο **αυστηρά** στα ευρήματα του Executor.

### 📁 Mini File Structure
```text
agentic-planner/
├── backend/                  
│   ├── core/                 # LangGraph Logic (Agents, Graph, Tools, Checkpointer)
│   ├── main.py               # FastAPI Streaming Server (Endpoints: /stream, /resume)
│   ├── requirements.txt      # Python Dependencies
│   └── Procfile / railway    # Deployment configs
└── frontend/                 
    ├── src/
    │   ├── App.jsx           # React UI & SSE Fetch Logic
    │   └── App.css           # Dark Theme & Animations Styling
    ├── package.json
    └── vite.config.js

```

---
## 💻 How to Run Locally

### 1. Backend (FastAPI)
Από τον φάκελο `backend/`:
```bash
python -m venv venv
# Ενεργοποίηση venv (Windows: .\venv\Scripts\activate)
pip install -r requirements.txt
```
*Φτιάξτε ένα `.env` αρχείο και προσθέστε το API key*
```bash
uvicorn main:app --reload --port 8001
```

### 2. Frontend (React/Vite)
Από τον φάκελο `frontend/`:
```bash
npm install
npm run dev
```
Ανοίξτε τον browser στο **http://localhost:5173**