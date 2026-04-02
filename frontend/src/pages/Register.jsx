import React, { useState } from "react";
import { registerUser } from "../services/authService";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleRegister = async () => {
    // ✅ Basic validation (existing - kept)
    if (!email || !password || !confirmPassword) {
      alert("All fields required");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    // 🔥 NEW: Email format validation (safe)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert("Enter valid email");
      return;
    }

    // 🔥 NEW: Password strength validation (minimal safe)
    if (password.length < 6) {
      alert("Password must be at least 6 characters");
      return;
    }

    try {
      await registerUser({
        email,
        password,
        confirm_password: confirmPassword // ✅ API contract matched
      });

      alert("Registered successfully");

      // ✅ SAME FLOW (UNCHANGED)
      navigate("/onboarding");

    } catch (err) {
      console.log(err);

      // 🔥 Slightly better error handling (safe)
      if (err.response?.data?.error) {
        alert(err.response.data.error);
      } else {
        alert("Registration failed");
      }
    }
  };

  // 🔥 STYLES (UNCHANGED)
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
        <h2>Register</h2>

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

        <input
          style={inputStyle}
          type="password"
          placeholder="Confirm password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
        <br /><br />

        <button style={buttonStyle} onClick={handleRegister}>
          Register
        </button>

        <br /><br />

        <p>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "#e60023", fontWeight: "bold" }}>
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

// This file creates the registration UI, validates inputs (email + password), sends correct API payload including confirm_password, handles errors safely, and redirects user to onboarding after successful registration