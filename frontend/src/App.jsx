import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Loader2, CheckCircle2, Circle, XCircle, BrainCircuit, User, Terminal, Play } from 'lucide-react';
import './App.css';

function App() { 
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [threadId] = useState(() => 'thread-' + Math.random().toString(36).substr(2, 9));
  
  // NEO: States για το Editable Plan
  const [isWaitingForApproval, setIsWaitingForApproval] = useState(false);
  const [editablePlan, setEditablePlan] = useState([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Βοηθητική συνάρτηση για το SSE Parsing (για να μην επαναλαμβανόμαστε)
  const processStream = async (reader, decoder, isResume = false) => {
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, '\n');
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); 

      for (const part of parts) {
        if (!part.trim()) continue;
        const lines = part.split('\n');
        let eventType = 'message';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event:')) eventType = line.replace('event:', '').trim();
          else if (line.startsWith('data:')) dataStr = line.substring(5).trim();
        }

        if (dataStr) {
          try {
            const data = JSON.parse(dataStr);
            
            if (eventType === 'waiting_for_user') {
                setIsWaitingForApproval(true);
                setEditablePlan(data.plan);
                setIsLoading(false); // Σταματάμε το loading γιατί περιμένουμε τον χρήστη
                continue;
            }

            setMessages(prev => {
              const newMessages = [...prev];
              const lastMsg = { ...newMessages[newMessages.length - 1] };

              if (eventType === 'plan_generated' || eventType === 'step_executed') {
                lastMsg.plan = Array.isArray(data.plan) ? data.plan : [];
              } else if (eventType === 'final_response') {
                lastMsg.content = data.response;
                lastMsg.isGenerating = false;
                setIsWaitingForApproval(false);

                if (lastMsg.plan) {
                  lastMsg.plan = lastMsg.plan.map(step => ({ ...step, status: 'completed' }));
                }
              } else if (eventType === 'log') {
                setLogs(prev => {
                  if (prev.some(log => log.id === data.id)) return prev; 
                  return [...prev, { id: data.id, timestamp: new Date().toLocaleTimeString(), message: data.message }];
                });
              } else if (eventType === 'error') {
                lastMsg.content = `❌ Σφάλμα: ${data.detail}`;
                lastMsg.isGenerating = false;
              }
              newMessages[newMessages.length - 1] = lastMsg;
              return newMessages;
            });
          } catch (e) { console.error("Parse Error", e); }
        }
      }
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    setInput('');
    setIsLoading(true);
    setIsWaitingForApproval(false);

    setLogs([{ timestamp: new Date().toLocaleTimeString(), message: "🚀 Εκκίνηση νέου αιτήματος..." }]);
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setMessages(prev => [...prev, { role: 'agent', content: '', plan: [], isGenerating: true }]);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const res = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, thread_id: threadId })
      });
      await processStream(res.body.getReader(), new TextDecoder('utf-8'));
    } catch (error) {
      console.error("Network Error:", error);
    } finally {
      // ΑΥΤΟ ΕΛΕΙΠΕ: Σταματάει το loading είτε πετύχει είτε αποτύχει!
      setIsLoading(false); 
    }
  };

  // NEO: Συνάρτηση για να στείλουμε το ΕΓΚΕΚΡΙΜΕΝΟ πλάνο πίσω
  const handleResume = async () => {
    setIsLoading(true);
    setIsWaitingForApproval(false);
    setLogs(prev => [...prev, { id: uuidv4(), timestamp: new Date().toLocaleTimeString(), message: "✅ Πλάνο εγκρίθηκε. Συνέχεια εκτέλεσης..." }]);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const res = await fetch(`${API_BASE_URL}/chat/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId, plan: editablePlan })
      });
      await processStream(res.body.getReader(), new TextDecoder('utf-8'), true);
    } catch (error) {
      console.error("Resume Error:", error);
    } finally {
      // ΑΥΤΟ ΕΛΕΙΠΕ ΚΑΙ ΕΔΩ!
      setIsLoading(false);
    }
  };

  const updatePlanStep = (idx, newText) => {
    const updated = [...editablePlan];
    updated[idx].description = newText;
    setEditablePlan(updated);
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'completed': return <CheckCircle2 size={18} color="#10b981" />;
      case 'in_progress': return <Loader2 size={18} color="#3b82f6" className="animate-spin" />;
      default: return <Circle size={18} color="#a1a1aa" />;
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Agentic Planner AI</h1>
        <button onClick={() => setShowLogs(!showLogs)} className={`logs-toggle-btn ${showLogs ? 'active' : ''}`}>
          <Terminal size={18} /> Developer Logs
        </button>
      </div>

      {showLogs && (
        <div className="logs-dashboard">
          <div className="logs-header">System Terminal</div>
          <div className="logs-content">
            {logs.map((log, idx) => (
              <div key={idx} className="log-line">
                <span className="log-time">[{log.timestamp}]</span> <span className="log-text">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="messages-area">
        {messages.map((msg, idx) => {
          const isLastMessage = idx === messages.length - 1;
          return (
            <div key={idx} className={`message ${msg.role}`}>
              <div className={`avatar ${msg.role}`}>
                {msg.role === 'user' ? <User size={20} /> : <BrainCircuit size={20} />}
              </div>
              
              <div className="message-content">
                {msg.role === 'agent' && Array.isArray(msg.plan) && msg.plan.length > 0 && (
                  <div className="plan-widget">
                    <div className="plan-header-row">
                        <div className="plan-title"><BrainCircuit size={16} /> Agent Execution Plan</div>
                        {isLastMessage && isWaitingForApproval && (
                            <span className="badge-waiting">Waiting for your Review</span>
                        )}
                    </div>

                    {/* Εδώ γίνεται η μαγεία: Αν περιμένουμε έγκριση, δείξε input fields */}
                    {(isLastMessage && isWaitingForApproval ? editablePlan : msg.plan).map((step, sIdx) => (
                      <div key={sIdx} className="plan-step">
                        <div className="step-status">{getStatusIcon(step.status)}</div>
                        <div className="step-desc">
                          <strong>Step {step.step_id}:</strong> 
                          {isLastMessage && isWaitingForApproval ? (
                             <textarea 
                                className="edit-plan-input"
                                value={step.description} 
                                onChange={(e) => {
                                  updatePlanStep(sIdx, e.target.value);
                                  // Auto-resize καθώς πληκτρολογεί ο χρήστης:
                                  e.target.style.height = 'auto';
                                  e.target.style.height = e.target.scrollHeight + 'px';
                                }}
                                // Auto-resize όταν εμφανίζεται για πρώτη φορά το κείμενο του Agent:
                                ref={(el) => {
                                  if (el) {
                                    el.style.height = 'auto';
                                    el.style.height = el.scrollHeight + 'px';
                                  }
                                }}
                                rows={1}
                              />
                          ) : (
                             <span> {step.description}</span>
                          )}
                          <br/><small>Tool: {step.tool}</small>
                        </div>
                      </div>
                    ))}

                    {isLastMessage && isWaitingForApproval && (
                        <button className="approve-btn" onClick={handleResume}>
                            <Play size={16} /> Approve & Continue Execution
                        </button>
                    )}
                  </div>
                )}

                {msg.content ? (
                  <div className="markdown-body"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                ) : (
                  msg.isGenerating && !isWaitingForApproval && <Loader2 size={24} className="animate-spin" style={{color: '#a1a1aa'}} />
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <form onSubmit={handleSend} className="input-form">
          <input 
            type="text" placeholder="Πες μου τι να κάνω..." 
            value={input} onChange={(e) => setInput(e.target.value)}
            disabled={isLoading || isWaitingForApproval}
          />
          <button type="submit" disabled={isLoading || isWaitingForApproval || !input.trim()}>
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </form>
      </div>
    </div>
  );
}

// Μικρό helper για το ID αν δεν έχεις uuid library
const uuidv4 = () => 'log-' + Math.random().toString(36).substr(2, 9);

export default App;