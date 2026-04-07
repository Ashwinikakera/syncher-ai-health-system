import axios from "axios";
import { getDashboard } from "./dashboardService";

export const askAI = async (question) => {
  try {
    // 🔥 STEP 1: Get dashboard risk safely
    let risk = "Unknown";

    try {
      const dashboard = await getDashboard();
      risk = dashboard?.data?.risk || "Unknown";
    } catch (err) {
      console.log("⚠️ Dashboard fetch failed:", err);
    }

    // 🔥 STEP 2: Build AI context
    const context = `
User Health Context:
- Risk Level: ${risk}

Give personalized menstrual health advice based on this.
`;

    // 🔥 STEP 3: Call Groq API
    const res = await axios.post(
      "https://api.groq.com/openai/v1/chat/completions",
      {
        model: "llama-3.1-8b-instant", // ✅ stable + fast
        messages: [
          {
            role: "system",
            content:
              "You are SYNCHER AI, a helpful assistant for menstrual health, hormones, cramps, and wellness. Give clear, simple, and safe advice."
          },
          {
            role: "user",
            content: `${context}\n\nUser Question: ${question}`
          }
        ],
        temperature: 0.7
      },
      {
        headers: {
          // ⚠️ IMPORTANT: Replace with NEW key (do not expose publicly)
          Authorization: `Bearer ${import.meta.env.VITE_GROQ_API_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    return {
      answer: res.data?.choices?.[0]?.message?.content || "No response"
    };

  } catch (err) {
    console.log("❌ FULL ERROR:", err.response?.data || err);

    return {
      answer: "AI service unavailable. Check API setup."
    };
  }
};

// This file sends user questions to chatbot API and receives AI-generated responses using axios, enabling Chatbot.jsx to provide personalized health insights based on backend ML and RAG system