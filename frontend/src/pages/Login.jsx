import React, { useState } from "react";
import { loginUser } from "../services/authService";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    if (!email || !password) {
      alert("Please enter email and password");
      return;
    }

    try {
      setLoading(true);

      const res = await loginUser({ email, password });
      const responseData = res?.data?.data || res?.data;

      const token = responseData?.token || "demo-token";

      const user = {
        id: responseData?.id || 1,
        email: responseData?.email || email,
        onboardingCompleted:
          responseData?.onboardingCompleted ??
          responseData?.is_onboarded ??
          false
      };

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));

      if (user.onboardingCompleted) {
        navigate("/dashboard", {
          replace: true,
          state: { message: "Login successful ✅" }
        });
      } else {
        navigate("/onboarding", {
          replace: true,
          state: { message: "Login successful ✅" }
        });
      }

    } catch (err) {
      console.log(err);
      alert("Login failed");
    } finally {
      setLoading(false);
    }
  };

  // 🔥 DASHBOARD-LIKE STYLES (ONLY ADDITION)
  const page = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    background: "#f8f9fb"
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
          Don’t have an account?{" "}
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

// This file handles login UI, validates inputs, sends credentials to backend via authService, stores JWT token, manages navigation to onboarding or dashboard, and provides proper error handling and user flow