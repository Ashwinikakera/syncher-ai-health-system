import React, { useState, useEffect } from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/dashboard";

import CycleLogger from "./components/cycleLogger";
import Logger from "./components/logger";
import Chatbot from "./components/chatbot";

import MyHealth from "./pages/MyHealth";

const styles = {
  app: {
    display: "flex",
    fontFamily: "Segoe UI",
    background: "#f8f9fb",
    height: "100vh"
  },

  // UPDATED SIDEBAR
  sidebar: {
    width: "220px",

    // FULL HEIGHT
    height: "100vh",

    // SCROLL ENABLE
    overflowY: "auto",

    // RED GRADIENT
    background: "#ffe5e5",

    color: "#fff",

    padding: "20px",
    boxSizing: "border-box",

    // FIX POSITION
    position: "fixed",
    left: 0,
    top: 0
  },

  // 🔥 SHIFT MAIN CONTENT
  main: {
    flex: 1,
    padding: "20px",
    marginLeft: "220px" // IMPORTANT FIX
  },

  // 🔴 MATCH NAVBAR COLOR
  navbar: {
    background: "linear-gradient(135deg, #ff4d4d, #ff1a1a)",
    color: "#fff",
    padding: "15px",
    borderRadius: "10px",
    marginBottom: "20px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
  }
};

function Layout({ children }) {
  const navigate = useNavigate();

  return (
    <div style={styles.app}>
      <div style={styles.sidebar}>
        <h2 style={{ color: "#ff4d4d" }}>SYNCHER</h2>

        <p style={{ cursor: "pointer", color: "black"}} onClick={() => navigate("/dashboard")}>
          Dashboard
        </p>

        <p style={{ cursor: "pointer", color: "black" }} onClick={() => navigate("/cycle-tracker")}>
          Cycle Tracker
        </p>

        <p style={{ cursor: "pointer", color: "black" }} onClick={() => navigate("/daily-logs")}>
          Daily Logs
        </p>

        <p style={{ cursor: "pointer", color: "black" }} onClick={() => navigate("/ai-assistant")}>
          AI Assistant
        </p>

        <p style={{ cursor: "pointer", color: "black" }} onClick={() => navigate("/my-health")}>
          My Health
        </p>

        <p
          style={{ color: "#ff4d4d", cursor: "pointer", marginTop: "20px", fontWeight: "bold" }}
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
        

        {children}
      </div>
    </div>
  );
}

function App() {
  const getValidToken = () => {
    const savedToken = localStorage.getItem("token");
    if (!savedToken || savedToken === "undefined" || savedToken === "null") {
      return null;
    }
    return savedToken;
  };

  const [token, setToken] = useState(getValidToken());

  useEffect(() => {
    const interval = setInterval(() => {
      const newToken = getValidToken();
      if (newToken !== token) {
        setToken(newToken);
      }
    }, 300);

    return () => clearInterval(interval);
  }, [token]);

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" />} />

      <Route
        path="/login"
        element={token ? <Navigate to="/dashboard" /> : <Login />}
      />

      <Route path="/register" element={<Register />} />
      <Route path="/onboarding" element={<Onboarding />} />

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

      <Route
        path="/my-health"
        element={
          token ? (
            <Layout>
              <MyHealth />
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