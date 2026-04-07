import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  timeout: 5000
});

// Attach token automatically
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

// FIX 3 — Real error handling, fallback only when server is completely down
API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (!err || !err.config) {
      return Promise.reject(err);
    }

    const url    = err.config?.url || "";
    const status = err.response?.status;

    // ── 401 Unauthorized — token expired or invalid ───────────────
    // Only redirect if NOT on login/register page
    if (status === 401) {
      if (!url.includes("/login") && !url.includes("/register")) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
      return Promise.reject(err);
    }

    // ── 400 Bad Request — show real error to user ─────────────────
    if (status === 400) {
      return Promise.reject(err);
    }

    // ── 500 Server Error — show real error ────────────────────────
    if (status === 500) {
      console.log("Server error on:", url, err.response?.data);
      return Promise.reject(err);
    }

    // ── No response at all — server is DOWN, use fallback ─────────
    if (!err.response) {
      console.log("⚠️ Server unreachable — using demo fallback for:", url);

      if (url.includes("/login")) {
        return Promise.resolve({
          data: { token: "demo-token", is_onboarded: false }
        });
      }
      if (url.includes("/register")) {
        return Promise.resolve({
          data: { message: "Registered successfully" }
        });
      }
      if (url.includes("/onboarding")) {
        return Promise.resolve({
          data: { message: "Onboarding completed" }
        });
      }
      if (url.includes("/dashboard")) {
        return Promise.resolve({
          data: {
            next_period_date:       "2024-04-25",
            ovulation_window:       ["2024-04-10", "2024-04-14"],
            cycle_regularity_score: 0.82,
            insights: [
              "Your cycle is fairly regular",
              "Maintain good sleep for better predictions"
            ]
          }
        });
      }
      if (url.includes("/chat")) {
        return Promise.resolve({
          data: {
            answer: "Your next period is likely around April 25 based on your cycle history."
          }
        });
      }
      if (url.includes("/cycle")) {
        return Promise.resolve({
          data: { cycles: [] }
        });
      }
      if (url.includes("/daily-log")) {
        return Promise.resolve({
          data: { logs: [] }
        });
      }
    }

    return Promise.reject(err);
  }
);

export default API;