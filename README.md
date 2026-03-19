# 🧠 Plan & Act Agent – Intern Project

**Assigned to:** Chris  
**Project Lead:** George Kotzamanis  
**API Key Contact:** George Kotzamanis  

---

## 📌 Project Overview

You will build an intelligent **Plan & Act Agent** — a system that:

1. Understands a user request  
2. Creates a structured plan  
3. Executes that plan step-by-step  
4. Returns a final, useful result  

This is **not just a chatbot**.  
It is an **agentic system** with planning, execution, and tool usage.

---

## 🎯 Core Capabilities

### ✅ 1. Plan Creation
Given a user query, the agent must generate a structured plan:
- Step-by-step
- Clear and logical
- Visible to the user

---

### ✅ 2. Plan Execution
The agent must:
- Execute each step
- Use tools when needed
- Iterate until completion

---

### ✅ 3. Agent Loop (Mandatory)

The system must follow this loop:

1. Understand request  
2. Generate plan  
3. Execute step  
4. Evaluate result  
5. Decide next step  
6. Repeat until completion  

---

### ✅ 4. Conversational Interface
- Chat-based UI
- Multi-turn conversations
- Memory of at least last **10 exchanges**

---

### ✅ 5. Internet Search
- The agent must be able to search the web during execution

---

## 🧰 Tools System

The agent must support a **tool layer**.

### Required Tool
- Web Search

### Optional Tools (Bonus)
- Calculator
- File Reader

### Tool Requirements
Each tool must:
- Have a clear input/output schema
- Be callable during execution
- Return structured outputs usable by the agent

👉 The system should be designed so **new tools can be added easily**

---

## 🧠 Architecture

### Preferred Pattern (Recommended)

A **multi-agent design** is encouraged:

- **Planner Agent**
  - Creates the plan

- **Executor Agent**
  - Executes steps one-by-one

---

### Optional (Advanced)
- Use an **A2A (Agent-to-Agent) communication pattern**

---

## 🖥️ Frontend Requirements

- Clean chatbot UI
- Responsive design

### Must Include

- ✅ Plan visibility (user sees plan before execution)
- ✅ Execution progress (current step, status)
- ✅ Final response clearly displayed
- ✅ Conversation memory
- ✅ **Streaming responses (real-time updates)**

---

## ⚙️ Backend Requirements

- OpenAI integration using: `gpt-4.1-mini`
- Tool execution system
- Plan generation logic
- Agent loop implementation
- Conversation history management
- API endpoints (if separate backend)

---

## 🔄 User Flow

1. User enters a query  
2. Agent generates a plan (visible)  
3. Agent executes steps (with progress updates)  
4. Agent returns final result  
5. User continues conversation  

---

## 💡 Example

### Input
> “Plan a 3-day trip to Tokyo and tell me what to pack”

### Plan
1. Check Tokyo weather  
2. Research travel packing recommendations  
3. Combine results  

---

## 📦 Plan Format (Required)

```json
[
  {
    "step_id": 1,
    "description": "Search Tokyo weather",
    "tool": "web_search",
    "status": "pending"
  }
]
```

---

## 📊 Execution Transparency

The user should see:

- Current step being executed
- Tool usage
- Progress updates

---

## 🧠 Memory

### Required
- Store last **10 messages**

---

## ❗ Error Handling

The system must:

- Retry failed tool calls (max 2 times)
- Handle API failures gracefully
- Inform the user clearly

---

## 🚀 Deployment Requirements

The project must be deployable on:

👉 **Railway**

### Must Include
- `.env.example`
- Setup instructions

---

## 🔐 Security Requirements

- ❌ No hardcoded API keys  
- ✅ Use environment variables  
- ❌ Never expose API keys in frontend  
- ✅ All OpenAI calls must go through backend  

---

## 🧪 Success Criteria

The project will be evaluated on:

- ✅ Plan quality
- ✅ Execution correctness
- ✅ UX clarity
- ✅ Code quality
- ✅ Deployment readiness

---

## 🎁 Bonus Features (Optional)

- Editable plan before execution  
- Multi-agent orchestration  
- Execution logs dashboard  

---

## 🏁 Getting Started

1. Choose architecture  
2. Build MVP  
3. Add tools  
4. Add streaming  
5. Deploy  

---

🚀 Build something you would proudly demo!
