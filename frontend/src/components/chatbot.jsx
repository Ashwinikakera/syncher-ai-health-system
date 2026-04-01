import React, { useState } from "react";
import { askChatbot } from "../services/chatService";

export default function Chatbot() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const handleAsk = async () => {
    try {
      const res = await askChatbot(question);
      setAnswer(res.data.answer);
    } catch (err) {
      console.log(err);
      setAnswer("AI not available (backend not connected)");
    }
  };

  return (
    <div>
      <h3>AI Assistant</h3>

      <input
        type="text"
        placeholder="Ask something..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <br /><br />

      <button onClick={handleAsk}>Ask</button>

      <p><strong>Answer:</strong> {answer}</p>
    </div>
  );
}

// This file builds chatbot UI that takes user queries, sends them to backend via chatService, receives AI-generated responses, and displays them enabling conversational interaction with ML/RAG system