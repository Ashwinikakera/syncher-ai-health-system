import React, { useState, useEffect } from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/dashboard";

import CycleLogger from "./components/cycleLogger";
import Logger from "./components/logger";
import Chatbot from "./components/chatbot";

const styles = {
  app: {
    display: "flex",
    fontFamily: "Segoe UI",
    background: "#f8f9fb",
    height: "100vh"
  },
  sidebar: {
    width: "220px",
    background: "#ffffff",
    padding: "20px",
    borderRight: "1px solid #eee"
  },
  main: {
    flex: 1,
    padding: "20px"
  },
  navbar: {
    background: "#fff",
    padding: "15px",
    borderRadius: "10px",
    marginBottom: "20px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.05)"
  }
};

function Layout({ children }) {
  const navigate = useNavigate();

  return (
    <div style={styles.app}>
      <div style={styles.sidebar}>
        <h2 style={{ color: "#e60023" }}>SYNCHER</h2>

        {/* ✅ FIXED NAVIGATION */}
        <p style={{ cursor: "pointer" }} onClick={() => navigate("/dashboard")}>
          Dashboard
        </p>

        <p style={{ cursor: "pointer" }} onClick={() => navigate("/cycle-tracker")}>
          Cycle Tracker
        </p>

        <p style={{ cursor: "pointer" }} onClick={() => navigate("/daily-logs")}>
          Daily Logs
        </p>

        <p style={{ cursor: "pointer" }} onClick={() => navigate("/ai-assistant")}>
          AI Assistant
        </p>

        {/* Logout */}
        <p
          style={{ color: "red", cursor: "pointer" }}
          onClick={() => {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "/login";
          }}
        >
          Logout
        </p>
      </div>

      <div style={styles.main}>
        <div style={styles.navbar}>
          <strong>Welcome Back 👋</strong>
        </div>

        {children}
      </div>
    </div>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));

  // 🔥 EXISTING WORKING LOGIC (UNCHANGED)
  useEffect(() => {
    const interval = setInterval(() => {
      const newToken = localStorage.getItem("token");
      if (newToken !== token) {
        setToken(newToken);
      }
    }, 300);

    return () => clearInterval(interval);
  }, [token]);

  return (
    <Routes>

      <Route path="/" element={<Navigate to="/login" />} />

      {/* LOGIN */}
      <Route
        path="/login"
        element={
          token ? <Navigate to="/dashboard" /> : <Login />
        }
      />

      {/* REGISTER */}
      <Route path="/register" element={<Register />} />

      {/* ONBOARDING */}
      <Route path="/onboarding" element={<Onboarding />} />

      {/* DASHBOARD */}
      <Route
        path="/dashboard"
        element={
          token ? (
            <Layout>
              <Dashboard />
            </Layout>
          ) : (
            <Navigate to="/login" />
          )
        }
      />

      {/* 🔥 NEW ROUTES ADDED (SAFE) */}

      <Route
        path="/cycle-tracker"
        element={
          token ? (
            <Layout>
              <CycleLogger />
            </Layout>
          ) : (
            <Navigate to="/login" />
          )
        }
      />

      <Route
        path="/daily-logs"
        element={
          token ? (
            <Layout>
              <Logger />
            </Layout>
          ) : (
            <Navigate to="/login" />
          )
        }
      />

      <Route
        path="/ai-assistant"
        element={
          token ? (
            <Layout>
              <Chatbot />
            </Layout>
          ) : (
            <Navigate to="/login" />
          )
        }
      />

    </Routes>
  );
}

export default App;

// This file defines routing with proper authentication checks, redirects users based on login state, and wraps protected pages inside a reusable layout with sidebar and navbar