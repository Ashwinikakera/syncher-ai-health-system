import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
  withCredentials: false,
  timeout: 5000
});

//  REQUEST INTERCEPTOR
API.interceptors.request.use(
  (req) => {
    try {
      console.log("🚀 API CALL:", req.url);

      let token = localStorage.getItem("token");

      //  AUTO CLEANUP
      if (token === "demo-token") {
        console.warn("⚠️ Removing demo-token");
        localStorage.removeItem("token");
        token = null;
      }

      // SEND TOKEN
      if (token) {
        req.headers.Authorization = `Bearer ${token}`;
        console.log("🔐 HEADER SENT:", req.headers.Authorization);
      } else {
        console.log("❌ No token found");
      }

    } catch (e) {
      console.log("Token read error:", e);
    }

    return req;
  },
  (error) => Promise.reject(error)
);

// RESPONSE INTERCEPTOR
API.interceptors.response.use(
  (res) => res,
  (err) => {
    console.log("⚠️ API error → checking fallback...");

    // 🔥 BACKEND ERROR → DO NOT FALLBACK
    if (err.response) {
      console.log("❌ Backend status:", err.response.status);
      console.log("📦 Backend data:", err.response.data);
      return Promise.reject(err);
    }

    // 🔥 ONLY NETWORK ERROR → fallback allowed
    if (err.code !== "ERR_NETWORK") {
      console.log("❌ Not a network error, skipping fallback");
      return Promise.reject(err);
    }

    const url = err.config?.url || "";
    console.log("🔄 Using fallback for:", url);

    // 🔥 LOGIN → NO FALLBACK
    if (url.includes("/login")) {
      console.log("🚫 Login fallback disabled");
      return Promise.reject(err);
    }

    // 🔥 CHAT → NO FALLBACK (IMPORTANT FOR ML)
    if (url.includes("/chat")) {
      console.log("🚫 Chat fallback disabled");
      return Promise.reject(err);
    }

    // 🔥 REGISTER
    if (url.includes("/register")) {
      return Promise.resolve({
        data: {
          message: "Registered successfully",
          onboardingCompleted: false
        }
      });
    }

    // 🔥 ONBOARDING
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

    // 🔥 Cycle
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

    // 🔥 Daily logs
    if (url.includes("/daily-log")) {
      return Promise.resolve({
        data: { logs: [] }
      });
    }

    console.log("❌ No fallback matched for:", url);

    return Promise.reject(err);
  }
);

export default API;

// ✅ Improvements:
// - Uses Bearer token for JWT (fixes 401)
// - Skips demo-token in real requests
// - Shows backend error data for debugging (very important)
// - Keeps fallback ONLY for network failures
// - Does NOT break any existing logic
