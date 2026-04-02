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

  // 🔥 SAME CARD STYLE
  const card = {
    background: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    maxWidth: "400px",
    margin: "40px auto",
    textAlign: "center"
  };

  // 🔥 SAME INPUT STYLE
  const inputStyle = {
    width: "100%",
    padding: "10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    boxSizing: "border-box"
  };

  // 🔥 SAME BUTTON STYLE
  const buttonStyle = {
    width: "100%",
    padding: "12px",
    background: "#e60023",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "bold"
  };

  return (
    <div style={card}>
      <h3>AI Assistant</h3>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

        <input
          style={inputStyle}
          type="text"
          placeholder="Ask something..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button style={buttonStyle} onClick={handleAsk}>
          Ask
        </button>

        {answer && (
          <div style={{
            marginTop: "10px",
            padding: "10px",
            background: "#f1f1f1",
            borderRadius: "6px",
            textAlign: "left"
          }}>
            <strong>Answer:</strong>
            <p style={{ marginTop: "5px" }}>{answer}</p>
          </div>
        )}

      </div>
    </div>
  );
}

// This file builds chatbot UI that takes user queries, sends them to backend via chatService, receives AI-generated responses, and displays them enabling conversational interaction with ML/RAG system