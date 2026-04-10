import React, { useState, useRef, useEffect } from "react";
import API from "../api/axios";

export default function AIAssistant() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [replyTo, setReplyTo] = useState(null);
  const bottomRef = useRef(null);

  // 🔽 LOAD OLD MESSAGES (SAFE)
  useEffect(() => {
    try {
      const savedMessages = sessionStorage.getItem("chat_messages");
      if (savedMessages) {
        setMessages(JSON.parse(savedMessages));
      }
    } catch (err) {
      console.log("Error loading chat:", err);
      sessionStorage.removeItem("chat_messages");
    }
  }, []);

  // 🔽 SAVE MESSAGES
  useEffect(() => {
    sessionStorage.setItem("chat_messages", JSON.stringify(messages));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      sender: "user",
      text: input,
      replyTo: replyTo || null
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setReplyTo(null);

    try {
      const res = await API.post("/chat/", {
        question: input
      });

      const botMessage = {
        sender: "bot",
        text: res?.data?.answer || "No response",
        replyTo: userMessage
      };

      setMessages((prev) => [...prev, botMessage]);

    } catch (err) {
      console.log("Chat error:", err);

      const errorMessage = {
        sender: "bot",
        text: "⚠️ AI unavailable",
        replyTo: userMessage
      };

      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  // 🎨 STYLES
  const container = {
    display: "flex",
    height: "100vh",
    background: "#ffe5e5"
  };

  const chatWrapper = {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    maxWidth: "1000px",
    margin: "0 auto",
    background: "#ffe5e5"
  };

  const header = {
    padding: "15px",
    background: "#ff2d2d",
    color: "#fff",
    fontWeight: "bold",
    textAlign: "center",
    fontSize: "18px",
    letterSpacing: "0.5px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
  };

  const chatBox = {
    flex: 1,
    overflowY: "auto",
    padding: "15px",
    display: "flex",
    flexDirection: "column"
  };

  const messageRow = (sender) => ({
    display: "flex",
    justifyContent: sender === "user" ? "flex-end" : "flex-start"
  });

  const bubble = (sender) => ({
    background: sender === "user" ? "#db7f82" : "#bb7878",
    padding: "8px 12px",
    borderRadius: "8px",
    margin: "4px 0",
    maxWidth: "65%",
    fontSize: "14px",
    cursor: "pointer",
    boxShadow: "0 1px 2px rgba(0,0,0,0.1)"
  });

  const replyBox = {
    fontSize: "12px",
    color: "#555",
    borderLeft: "3px solid #34b7f1",
    paddingLeft: "6px",
    marginBottom: "4px"
  };

  const inputArea = {
    display: "flex",
    padding: "10px",
    background: "#bb7878"
  };

  const inputStyle = {
    flex: 1,
    padding: "10px",
    borderRadius: "20px",
    border: "none",
    outline: "none"
  };

  const sendBtn = {
    marginLeft: "10px",
    padding: "10px 15px",
    borderRadius: "50%",
    background: "#d32542",
    color: "#fff",
    border: "none",
    cursor: "pointer"
  };

  return (
    <div style={container}>
      <div style={chatWrapper}>

        {/* 🔥 HEADER */}
        <div style={header}>
          AI Assistant 🤖
        </div>

        {/* 💬 CHAT */}
        <div style={chatBox}>
          {messages.map((msg, index) => (
            <div key={index} style={messageRow(msg.sender)}>
              <div
                style={bubble(msg.sender)}
                onClick={() => setReplyTo(msg)}
              >
                {msg.replyTo && (
                  <div style={replyBox}>
                    {msg.replyTo.text.slice(0, 40)}
                  </div>
                )}
                {msg.text}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* 🔁 REPLY PREVIEW */}
        {replyTo && (
          <div style={{
            padding: "8px 12px",
            background: "#d9fdd3",
            fontSize: "13px"
          }}>
            Replying to: {replyTo.text.slice(0, 60)}

            <span
              style={{ float: "right", cursor: "pointer" }}
              onClick={() => setReplyTo(null)}
            >
              ❌
            </span>
          </div>
        )}

        {/* ⌨️ INPUT */}
        <div style={inputArea}>
          <input
            style={inputStyle}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message"
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />

          <button style={sendBtn} onClick={handleSend}>
            ➤
          </button>
        </div>

      </div>
    </div>
  );
}

// This file builds chatbot UI that takes user queries, sends them to backend via chatService, receives AI-generated responses, and displays them enabling conversational interaction with ML/RAG system