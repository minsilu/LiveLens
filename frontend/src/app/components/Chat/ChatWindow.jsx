import React, { useState } from 'react';
import './ChatWindow.css';

const ChatWindow = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleSend = async () => {
    if (input.trim() === '') return;

    const userMessage = { sender: 'user', text: input };
    setMessages([...messages, userMessage]);
    setInput('');

    // TODO: Call backend API
    const botMessage = { sender: 'bot', text: 'This is a response from the bot.' };
    setMessages(prevMessages => [...prevMessages, botMessage]);
  };

  if (!isOpen) {
    return (
      <button onClick={toggleChat} className="chat-toggle-button">
        Chat
      </button>
    );
  }

  return (
    <div className="chat-window">
      <div className="chat-header" onClick={toggleChat}>
        <h2>Chat with us</h2>
        <button className="close-chat">x</button>
      </div>
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default ChatWindow;
