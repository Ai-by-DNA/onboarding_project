import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Loader2, CheckCircle2, Circle, XCircle, BrainCircuit, User } from 'lucide-react';
import './App.css';

function App() { 
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    setInput('');
    setIsLoading(true);

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setMessages(prev => [...prev, { role: 'agent', content: '', plan: [], isGenerating: true }]);

    try {
      const res = await fetch('http://localhost:8001/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, thread_id: "default-thread" })
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        // 1. Διαβάζω το κομμάτι
        buffer += decoder.decode(value, { stream: true });
        
        // 2. Μετατρέπω όλα τα \r\n των Windows σε απλά \n
        buffer = buffer.replace(/\r\n/g, '\n');
        
        // 3. Χωρίζω τα events
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); 

        for (const part of parts) {
          if (!part.trim()) continue; // Αν είναι άδειο, το αγνοούμε

          const lines = part.split('\n');
          let eventType = 'message';
          let dataStr = '';

          // 4. (δεν μας νοιάζει η σειρά των γραμμών)
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              dataStr = line.substring(5).trim();
            }
          }

          if (dataStr) {
            console.log(`[React Διάβασε] Event: ${eventType}`, dataStr);

            try {
              const data = JSON.parse(dataStr);

              setMessages(prev => {
                const newMessages = [...prev];
                const lastMsg = { ...newMessages[newMessages.length - 1] };

                if (eventType === 'plan_generated' || eventType === 'step_executed') {
                  lastMsg.plan = Array.isArray(data.plan) ? data.plan : [];
                } else if (eventType === 'final_response') {
                  lastMsg.content = typeof data.response === 'string' ? data.response : JSON.stringify(data.response);
                  lastMsg.isGenerating = false;
                } else if (eventType === 'error') {
                  lastMsg.content = `❌ Σφάλμα Backend: ${data.detail}`;
                  lastMsg.isGenerating = false;
                }

                newMessages[newMessages.length - 1] = lastMsg;
                return newMessages;
              });
            } catch (parseError) {
              console.error("JSON Parse Error:", parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error("Network Error:", error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1].content = "⚠️ Υπήρξε ένα σφάλμα κατά την επικοινωνία με τον Server.";
        newMsgs[newMsgs.length - 1].isGenerating = false;
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'completed': return <CheckCircle2 size={18} color="#10b981" />;
      case 'in_progress': return <Loader2 size={18} color="#3b82f6" className="animate-spin" />;
      case 'failed': return <XCircle size={18} color="#ef4444" />;
      default: return <Circle size={18} color="#a1a1aa" />;
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Agentic Planner AI</h1>
      </div>

      <div className="messages-area">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className={`avatar ${msg.role}`}>
              {msg.role === 'user' ? <User size={20} /> : <BrainCircuit size={20} />}
            </div>
            
            <div className="message-content">
              {/* SAFETY CHECK: Array.isArray */}
              {msg.role === 'agent' && Array.isArray(msg.plan) && msg.plan.length > 0 && (
                <div className="plan-widget">
                  <div className="plan-title">
                    <BrainCircuit size={16} /> Agent Execution Plan
                  </div>
                  {msg.plan.map((step, sIdx) => (
                    <div key={sIdx} className="plan-step">
                      <div className="step-status">{getStatusIcon(step.status)}</div>
                      <div className="step-desc">
                        <strong>Βήμα {step.step_id}:</strong> {step.description}
                        <br/>
                        <small style={{color: '#71717a'}}>Εργαλείο: {step.tool}</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* SAFETY CHECK: typeof string */}
              {msg.content && typeof msg.content === 'string' ? (
                <div className="markdown-body">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.isGenerating && <Loader2 size={24} className="animate-spin" style={{color: '#a1a1aa'}} />
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <form onSubmit={handleSend} className="input-form">
          <input 
            type="text" 
            placeholder="Δώσε μου έναν στόχο..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;