import { useState, useRef, useEffect } from "react";
import { X, Send, Sparkles } from "lucide-react";

export function GlobalChatPanel({ isOpen, onClose }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/ai/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_data: userText,
          instructions:
            "You are a helpful assistant for LiveLens, a venue review platform. Answer general questions about venues, events, seating, and concert experiences. If the user asks about a specific venue, use the available DB functions to fetch real data. Never use markdown formatting — plain text only.",
        }),
      });

      if (!response.ok) throw new Error("API Error");
      const data = await response.json();
      setMessages((prev) => [...prev, { sender: "bot", text: data.analysis }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, I'm having trouble connecting. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40"
          onClick={onClose}
        />
      )}

      {/* Side panel */}
      <div
        className={`fixed top-0 right-0 h-full w-96 max-w-[100vw] bg-gray-900 border-l border-gray-700/50 shadow-2xl z-50 flex flex-col transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700/50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-white font-semibold">Ask AI</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors rounded-lg hover:bg-gray-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Messages */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto px-4 py-4 space-y-3"
        >
          {messages.length === 0 && (
            <div className="text-center text-gray-500 text-sm mt-8 space-y-3">
              <Sparkles className="w-8 h-8 text-blue-400/50 mx-auto" />
              <p>Ask me anything about venues, events, or seating.</p>
              <div className="space-y-2 text-left">
                {[
                  "What are the top rated venues?",
                  "Which venue has the best sound?",
                  "What events are coming up at MSG?",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="w-full text-left px-3 py-2 rounded-lg bg-gray-800/60 hover:bg-gray-700/60 text-gray-400 hover:text-gray-200 text-xs transition-colors border border-gray-700/50"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                  msg.sender === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-200"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 px-3 py-2 rounded-xl text-sm text-gray-400">
                <span className="animate-pulse">...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-4 py-4 border-t border-gray-700/50 flex-shrink-0">
          <div className="flex items-center gap-2 bg-gray-800/60 border border-gray-700/50 rounded-xl px-3 py-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask anything..."
              className="flex-1 bg-transparent text-white placeholder-gray-500 text-sm focus:outline-none"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors flex-shrink-0"
            >
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
