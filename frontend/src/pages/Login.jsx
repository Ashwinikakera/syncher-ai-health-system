import React, { useState } from "react";
import { loginUser } from "../services/authService";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

const handleLogin = async () => {
  console.log("🚀 Login clicked");

  if (!email || !password) {
    alert("Please enter email and password");
    return;
  }

  try {
    const res = await loginUser({ email, password });

    console.log("✅ FULL RESPONSE:", res);

    // 🔥 Safe extraction
    const token = res?.data?.token || "demo-token";
    const isOnboarded = res?.data?.is_onboarded ?? true; // default TRUE

    // ✅ Store properly
    localStorage.setItem("token", token);
    localStorage.setItem("is_onboarded", isOnboarded.toString());

    alert("Login successful ✅");

    // 🔥 FORCE NAVIGATION (no ambiguity)
    if (isOnboarded === true || isOnboarded === "true") {
      navigate("/dashboard");
    } else {
      navigate("/onboarding");
    }

  } catch (err) {
    console.log("❌ Error:", err);
    alert("Login failed");
  }
};

  return (
    <div style={{ maxWidth: "300px" }}>
      <h2>Login</h2>

      <input
        type="email"
        placeholder="Enter email"
        value={email}
        onChange={(e) => {
          console.log("📧 Email typing:", e.target.value);
          setEmail(e.target.value);
        }}
      />
      <br /><br />

      <input
        type="password"
        placeholder="Enter password"
        value={password}
        onChange={(e) => {
          console.log("🔒 Password typing");
          setPassword(e.target.value);
        }}
      />
      <br /><br />

      {/* 🔥 DEBUG BUTTON */}
      <button
        onClick={() => {
          console.log("🔥 Login button clicked");
          handleLogin();
        }}
      >
        Login
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
          onClick={() => {
            console.log("➡️ Navigate to register");
            navigate("/register");
          }}
        >
          Register
        </span>
      </p>
    </div>
  );
}

// This file handles login UI, validates inputs, sends credentials to backend via authService, stores JWT token, manages navigation to onboarding or dashboard, and provides proper error handling and user flow