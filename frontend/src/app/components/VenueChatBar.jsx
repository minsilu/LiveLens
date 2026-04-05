import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, ChevronDown } from "lucide-react";

export function VenueChatBar({ venueName, venueId }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  useEffect(() => {
    if (isExpanded && messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, isExpanded]);

  async function handleSend() {
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");
    setIsExpanded(true);
    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/ai/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_data: { question: userText, venue_name: venueName, venue_id: venueId },
          instructions: `You are a helpful venue assistant for ${venueName}. Always use the DB functions before answering. Never guess or fabricate ratings, reviews, or events.`,
        }),
      });

      if (!response.ok) throw new Error("API Error");
      const data = await response.json();
      setMessages((prev) => [...prev, { sender: "bot", text: data.analysis }]);
    } catch {
      setMessages((prev) => [...prev, { sender: "bot", text: "Sorry, I'm having trouble connecting. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl overflow-hidden mb-6">
      {/* Input bar */}
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="flex items-center gap-2 text-blue-400 flex-shrink-0">
          <Sparkles className="w-4 h-4" />
          <span className="text-sm font-medium text-gray-300 hidden sm:block">Ask AI</span>
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={`Ask anything about ${venueName}...`}
          className="flex-1 bg-transparent text-white placeholder-gray-500 text-sm focus:outline-none"
        />
        <div className="flex items-center gap-2 flex-shrink-0">
          {messages.length > 0 && (
            <button
              onClick={() => setIsExpanded((v) => !v)}
              className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
            </button>
          )}
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      {/* Messages panel */}
      {isExpanded && messages.length > 0 && (
        <div ref={messagesContainerRef} className="border-t border-gray-700/50 px-4 py-3 max-h-64 overflow-y-auto space-y-3">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                msg.sender === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700/60 text-gray-200"
              }`}>
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-700/60 px-3 py-2 rounded-xl text-sm text-gray-400">
                <span className="animate-pulse">...</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
