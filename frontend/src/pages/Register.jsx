import React, { useState } from "react";
import { registerUser } from "../services/authService";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleRegister = async () => {
    if (!email || !password || !confirmPassword) {
      alert("All fields required");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    try {
      await registerUser({
        email,
        password,
        confirm_password: confirmPassword
      });

      alert("Registered successfully");

      // 🔥 Go to onboarding immediately
      navigate("/onboarding");

    } catch (err) {
      console.log(err);
      alert("Registration failed");
    }
  };

  return (
    <div style={{ maxWidth: "300px" }}>
      <h2>Register</h2>

      <input
        type="email"
        placeholder="Enter email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <br /><br />

      <input
        type="password"
        placeholder="Enter password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <br /><br />

      <input
        type="password"
        placeholder="Confirm password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />
      <br /><br />

      <button onClick={handleRegister}>Register</button>

      <br /><br />

      <p>
        Already have an account?{" "}
        <Link to="/">Login</Link>
      </p>
    </div>
  );
}

// This file creates the registration UI, collects user details, sends them to backend via authService, handles success/failure flow, and redirects to login page enabling user account creation process