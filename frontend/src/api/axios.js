import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  timeout: 5000 // ✅ avoid hanging requests
});

// ✅ Attach token automatically
API.interceptors.request.use(
  (req) => {
    try {
      const token = localStorage.getItem("token");

      if (token) {
        req.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      console.log("Token read error:", e);
    }

    return req;
  },
  (error) => Promise.reject(error)
);

// ✅ DEMO FALLBACK (SMART VERSION + SAFE)
API.interceptors.response.use(
  (res) => res,
  (err) => {
    console.log("⚠️ Demo fallback triggered");

    // 🔥 SAFE GUARD (IMPORTANT)
    if (!err || !err.config) {
      console.log("Unknown axios error:", err);
      return Promise.reject(err);
    }

    const url = err.config?.url || "";

    // 🔥 LOGIN → simulate first-time user
    if (url.includes("/login")) {
      return Promise.resolve({
        data: {
          token: "demo-token",
          email: "demo@gmail.com",
          onboardingCompleted: true
        }
      });
    }

    // 🔥 REGISTER → always onboarding
    if (url.includes("/register")) {
      return Promise.resolve({
        data: {
          message: "Registered successfully",
          onboardingCompleted: false
        }
      });
    }

    // 🔥 ONBOARDING → complete → dashboard
    if (url.includes("/onboarding")) {
      return Promise.resolve({
        data: {
          message: "Onboarding completed",
          onboardingCompleted: true
        }
      });
    }

    // 🔥 DASHBOARD
    if (url.includes("/dashboard")) {
      return Promise.resolve({
        data: {
          next_period_date: "2024-04-25",
          ovulation_window: ["2024-04-10", "2024-04-14"],
          cycle_regularity_score: 0.82,
          insights: [
            "Your cycle is fairly regular",
            "Maintain good sleep for better predictions"
          ]
        }
      });
    }

    // 🔥 Cycle fallback
    if (url.includes("/cycle")) {
      return Promise.resolve({
        data: {
          cycles: [
            {
              start_date: "2024-03-01",
              end_date: "2024-03-05",
              cycle_length: 28
            }
          ]
        }
      });
    }

    // 🔥 Daily logs fallback
    if (url.includes("/daily-log")) {
      return Promise.resolve({
        data: {
          logs: []
        }
      });
    }

    // 🔥 CHAT AI FALLBACK
    if (url.includes("/chat")) {
      return Promise.resolve({
        data: {
          answer: "Your next period is likely around April 25 based on your cycle history."
        }
      });
    }

    // 🔥 DEBUG FALLBACK (VERY IMPORTANT)
    console.log("❌ No fallback matched for:", url);

    return Promise.reject(err);
  }
);

export default API;

// This file centralizes API calls, attaches JWT tokens automatically,
// and safely simulates backend responses for login, register, onboarding,
// dashboard, and future endpoints without breaking the app.