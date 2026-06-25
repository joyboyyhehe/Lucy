import { useState, useRef, useEffect } from "react";
import "./App.css";

interface Message {
  id: string;
  sender: "user" | "lucy";
  text: string;
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "lucy",
      text: "Hello! I am Lucy, your desktop companion. Ask me anything, or type a command to see how I can help.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessageText = input;
    const userMsg: Message = {
      id: Math.random().toString(36).substring(2, 9),
      sender: "user",
      text: userMessageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessageText,
          session_id: "default-session",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to communicate with FastAPI backend");
      }

      const data = await response.json();
      
      const lucyMsg: Message = {
        id: Math.random().toString(36).substring(2, 9),
        sender: "lucy",
        text: data.response,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, lucyMsg]);
    } catch (err) {
      console.error(err);
      const errMsg: Message = {
        id: Math.random().toString(36).substring(2, 9),
        sender: "lucy",
        text: "Error: I couldn't reach my local brain. Make sure the FastAPI server is running on port 8000.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-title">
          <span className="dot active"></span>
          <h1>Lucy AI</h1>
        </div>
        <div className="header-status">
          <span>System: Healthy</span>
          <span className="separator">|</span>
          <span>FastAPI: 8000</span>
        </div>
      </header>

      <div className="chat-window">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-bubble ${msg.sender === "user" ? "user-bubble" : "lucy-bubble"}`}
          >
            <div className="bubble-sender">{msg.sender === "user" ? "You" : "Lucy"}</div>
            <div className="bubble-text">{msg.text}</div>
            <div className="bubble-time">
              {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-bubble lucy-bubble loading-bubble">
            <span className="dot-flashing"></span>
            <span className="dot-flashing"></span>
            <span className="dot-flashing"></span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Lucy to open YouTube, run code, or find files..."
          disabled={isLoading}
          autoFocus
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;
