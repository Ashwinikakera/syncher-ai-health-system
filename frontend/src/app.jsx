import React from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/dashboard";

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
      {/* Sidebar */}
      <div style={styles.sidebar}>
        <h2 style={{ color: "#e60023" }}>SYNCHER</h2>

        <p onClick={() => navigate("/dashboard")}>Dashboard</p>
        <p>Cycle Tracker</p>
        <p>Daily Logs</p>
        <p>AI Assistant</p>

        {/* Logout */}
        <p
          style={{ color: "red", cursor: "pointer" }}
          onClick={() => {
            localStorage.removeItem("token");
            window.location.href = "/login";
          }}
        >
          Logout
        </p>
      </div>

      {/* Main */}
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
  const token = localStorage.getItem("token");

  return (
    <Routes>

      {/* Default Route */}
      <Route
        path="/"
        element={<Navigate to="/login" />}
      />

      {/* Login */}
      <Route
        path="/login"
        element={
          token ? <Navigate to="/dashboard" /> : <Login />
        }
      />

      {/* Register */}
      <Route path="/register" element={<Register />} />

      {/* Onboarding */}
      <Route
        path="/onboarding"
        element={
          token ? (
            <Layout>
              <Onboarding />
            </Layout>
          ) : (
            <Navigate to="/login" />
          )
        }
      />

      {/* Dashboard */}
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

    </Routes>
  );
}

export default App;

// This file defines routing with proper authentication checks, redirects users based on login state, and wraps protected pages inside a reusable layout with sidebar and navbar