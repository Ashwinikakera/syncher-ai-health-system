<<<<<<< HEAD
=======
import React, { useState } from "react";
import { loginUser } from "../services/authService";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async () => {
    console.log(" LOGIN BUTTON CLICKED");

    if (!email || !password) {
      alert("Please enter email and password");
      return;
    }

    try {
      setLoading(true);

      console.log("📡 Calling login API...");

      const res = await loginUser({ email, password });

      console.log("✅ LOGIN RESPONSE FULL:", res.data);

      const responseData = res?.data?.data || res?.data;

      const token =
        responseData?.access ||
        responseData?.token ||
        res?.data?.access ||
        null;

      if (!token) {
        console.log("❌ No token from backend:", responseData);
        alert("Login failed: No token received");
        return;
      }

      // SMART DEFAULT
      const onboardingCompleted =
        responseData?.onboardingCompleted === true ||
        responseData?.is_onboarded === true;

      const user = {
        id: responseData?.id || 1,
        email: responseData?.email || email,
        onboardingCompleted: onboardingCompleted
      };

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));

      console.log("🔐 TOKEN:", token);
      console.log("👤 USER:", user);

      // ✅ FIX: reversed navigation logic
      // is_onboarded = false → new user → go to onboarding
      // is_onboarded = true  → existing user → go to dashboard
      if (responseData?.is_onboarded) {
        navigate("/dashboard", { replace: true });
      } else {
        navigate("/onboarding", { replace: true });
      }

    } catch (err) {
        console.log("❌ Login error:", err.response?.data || err);

        const message =
          err?.response?.data?.error ||
          err?.response?.data?.detail ||
          "Invalid email or password";

        alert(message);
      } finally {
      setLoading(false);
    }
  };

  // UI unchanged
  const page = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    background: "#ffe5e5"
  };

  const card = {
    background: "#fff",
    padding: "30px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    width: "320px",
    textAlign: "center"
  };

  const inputStyle = {
    width: "100%",
    padding: "10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px"
  };

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
    <div style={page}>
      <div style={card}>
        <h2>Login</h2>

        <input
          style={inputStyle}
          type="email"
          placeholder="Enter email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <br /><br />

        <input
          style={inputStyle}
          type="password"
          placeholder="Enter password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <br /><br />

        <button style={buttonStyle} onClick={handleLogin} disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>

        <br /><br />

        <p>
          Don't have an account?{" "}
          <span
            style={{
              color: "#e60023",
              cursor: "pointer",
              fontWeight: "bold"
            }}
            onClick={() => navigate("/register")}
          >
            Register
          </span>
        </p>
      </div>
    </div>
  );
}

// This file now:
// ✅ Uses ONLY real backend token
// ✅ Prevents fake login
// ✅ Fixes 401 Unauthorized issue
// ✅ Fixes navigation — new users go to onboarding, existing to dashboard
// ✅ Keeps UI and flow unchanged
>>>>>>> 0b61d3502123e67d9b4d3a9c911c1f3faf0ff4ee
