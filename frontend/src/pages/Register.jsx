import React, { useState } from "react";
import { registerUser } from "../services/authService";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [username, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleRegister = async () => {
    // ✅ FIXED validation
    if (!username || !email || !password || !confirmPassword) {
      alert("All fields required");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert("Enter valid email");
      return;
    }

    if (password.length < 6) {
      alert("Password must be at least 6 characters");
      return;
    }

    try {
      await registerUser({
        username,
        email,
        password,
        confirm_password: confirmPassword
      });

      alert("Registered successfully");
      navigate("/onboarding");

    } catch (err) {
      console.log(err);

      if (err.response?.data?.error) {
        alert(err.response.data.error);
      } else {
        alert("Registration failed");
      }
    }
  };

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
        <h2>Register</h2>

        {/* ✅ FIXED HERE */}
        <input
          style={inputStyle}
          type="text"
          placeholder="Enter Name"
          value={username}
          onChange={(e) => setName(e.target.value)}
        />
        <br /><br />

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
