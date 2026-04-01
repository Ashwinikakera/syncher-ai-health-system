import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
});

// ✅ Attach token automatically
API.interceptors.request.use((req) => {
  const token = localStorage.getItem("token");
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

// ✅ DEMO FALLBACK
API.interceptors.response.use(
  (res) => res,
  (err) => {
    console.log("⚠️ Demo fallback triggered");

    const url = err.config?.url;

    // 🔥 LOGIN → go to dashboard
    if (url?.includes("/login")) {
      return Promise.resolve({
        data: {
          token: "demo-token",
          is_onboarded: true   // ✅ Always onboarded → dashboard
        }
      });
    }

    // 🔥 REGISTER → force onboarding
    if (url?.includes("/register")) {
      return Promise.resolve({
        data: {
          message: "Registered successfully",
          is_onboarded: false
        }
      });
    }

    // 🔥 ONBOARDING → complete and go dashboard
    if (url?.includes("/onboarding")) {
      return Promise.resolve({
        data: {
          message: "Onboarding completed",
          is_onboarded: true
        }
      });
    }

    return Promise.reject(err);
  }
);

export default API;

// This axios setup simulates full user flow: login → dashboard, register → onboarding → dashboard, and maintains token-based API communication.