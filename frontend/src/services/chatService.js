import API from "../api/axios";

export const askChatbot = (question) =>
  API.post("/chat", { question });

// This file sends user questions to chatbot API and receives AI-generated responses using axios, enabling Chatbot.jsx to provide personalized health insights based on backend ML and RAG system