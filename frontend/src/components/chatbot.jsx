import React, { useState } from "react";
import { askAI } from "../services/chatService";

export default function Chatbot() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question) {
      alert("Please enter a question");
      return;
    }

    try {
      setLoading(true);
      setAnswer("Thinking... 🤖");

      console.log("🧠 Question:", question);

      // 🔥 DIRECT AI CALL (NO KEYWORD LOGIC)
      const res = await askAI(question);

      console.log("🤖 AI Response:", res);

      const aiAnswer =
        res?.answer ||
        res?.response ||
        res?.message ||
        res?.data?.answer ||
        res?.data?.response ||
        "I couldn't understand. Please try again.";

      setAnswer(aiAnswer);

    } catch (err) {
      console.log("❌ Chat error:", err);
      setAnswer("Error getting response from AI ❌");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={card}>
      <h3>AI Assistant</h3>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <input
          style={inputStyle}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your menstrual health..."
        />

        <button style={buttonStyle} onClick={handleAsk} disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      <div style={{ marginTop: "15px" }}>
        <b>Answer:</b>
        <p>{answer}</p>
      </div>
    </div>
  );
}

// styles (UNCHANGED)
// 🔥 UPDATED CARD (WIDER + CLEAN)
const card = {
  background: "#fff",
  padding: "30px",
  borderRadius: "12px",
  boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  maxWidth: "700px", // 🔥 increased from 400 → 700
  width: "100%",
  margin: "40px auto",
  textAlign: "center"
};

// 🔥 INPUT
const inputStyle = {
  width: "100%",
  padding: "12px",
  borderRadius: "6px",
  border: "1px solid #ccc",
  fontSize: "14px"
};

// 🔥 BUTTON
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

// 🔥 NEW ANSWER BOX
const answerBox = {
  marginTop: "20px",
  textAlign: "left"
};

// 🔥 SCROLLABLE + CLEAN TEXT
const answerText = {
  background: "#f9f9f9",
  padding: "15px",
  borderRadius: "8px",
  maxHeight: "250px", // 🔥 prevents overflow
  overflowY: "auto",
  lineHeight: "1.6",
  fontSize: "14px",
  whiteSpace: "pre-wrap"
};

// This file builds chatbot UI that takes user queries, sends them to backend via chatService, receives AI-generated responses, and displays them enabling conversational interaction with ML/RAG system