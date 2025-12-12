import { useState, useEffect, useRef } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Icons as components
const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
  </svg>
);

const UploadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
  </svg>
);

const BotIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="8" width="18" height="12" rx="2" />
    <circle cx="9" cy="14" r="2" />
    <circle cx="15" cy="14" r="2" />
    <path d="M12 2v4M6 8V6a2 2 0 012-2h8a2 2 0 012 2v2" />
  </svg>
);

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState('loading');
  const [toast, setToast] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Check API health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/health`);
      if (res.ok) {
        setHealthStatus('healthy');
      } else {
        setHealthStatus('unhealthy');
      }
    } catch {
      setHealthStatus('unhealthy');
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputValue };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: inputValue }),
      });

      if (!res.ok) throw new Error('Failed to get response');

      const data = await res.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      showToast('Failed to get response. Please try again.', 'error');
      console.error('Query error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });
    formData.append('policy_name', 'AML Policy');
    formData.append('jurisdiction', 'Global');
    formData.append('version', '1.0');

    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/ingest`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await res.json();
      showToast(`Successfully uploaded ${data.documents_processed} document(s)!`, 'success');
    } catch (error) {
      showToast(error.message || 'Failed to upload documents', 'error');
      console.error('Upload error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFileUpload(e.dataTransfer.files);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>AML Policy FAQ Bot</h1>
        <p>Ask questions about Anti-Money Laundering policies and compliance</p>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          {/* Upload Card */}
          <div className="card">
            <h3>Upload Documents</h3>
            <div
              className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <UploadIcon />
              <p>Drag & drop or <span>browse</span></p>
              <p style={{ fontSize: '0.75rem', marginTop: '4px' }}>PDF, DOC, DOCX</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx"
              multiple
              style={{ display: 'none' }}
              onChange={(e) => handleFileUpload(e.target.files)}
            />
          </div>

          {/* Status Card */}
          <div className="card">
            <h3>API Status</h3>
            <div className="health-indicator">
              <span className={`health-dot ${healthStatus}`}></span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                {healthStatus === 'healthy' ? 'Connected' :
                  healthStatus === 'loading' ? 'Checking...' : 'Disconnected'}
              </span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h3>Quick Questions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                'What is AML?',
                'KYC requirements?',
                'Suspicious activity reporting?',
              ].map((q, i) => (
                <button
                  key={i}
                  className="btn btn-secondary"
                  style={{ textAlign: 'left', fontSize: '0.8rem' }}
                  onClick={() => setInputValue(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Chat Window */}
        <div className="chat-window">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                <BotIcon />
                <h3 style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>
                  Start a conversation
                </h3>
                <p style={{ marginTop: '8px', fontSize: '0.9rem' }}>
                  Ask questions about AML policies, compliance requirements, or upload documents to analyze.
                </p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'assistant' ? '🤖' : '👤'}
                </div>
                <div className="message-content">
                  <p>{msg.content}</p>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources">
                      <div className="sources-title">Sources</div>
                      {msg.sources.map((src, i) => (
                        <div key={i} className="source-item">
                          {src.source || src.document_name || 'Policy Document'}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form className="chat-input-container" onSubmit={handleSubmit}>
            <div className="chat-input-wrapper">
              <textarea
                className="chat-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Ask a question about AML policies..."
                rows={1}
              />
              <button type="submit" className="send-button" disabled={isLoading || !inputValue.trim()}>
                <SendIcon />
              </button>
            </div>
          </form>
        </div>
      </main>

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

export default App;
