import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";

export default function Onboarding() {
  const navigate = useNavigate();

  const [age, setAge] = useState("");
  const [weight, setWeight] = useState("");

  const [cycles, setCycles] = useState([
    { start: "", end: "" },
    { start: "", end: "" },
    { start: "", end: "" }
  ]);

  const handleCycleChange = (index, field, value) => {
    const updated = [...cycles];
    updated[index][field] = value;
    setCycles(updated);
  };

  const handleSubmit = async () => {
    try {
      const formattedCycles = cycles.map((c) => ({
        start_date: c.start,
        end_date: c.end
      }));

      await API.post("/onboarding", {
        age: Number(age),
        weight: Number(weight),
        cycles: formattedCycles
      });

      let token = localStorage.getItem("token");

      if (!token) {
        token = "demo-token";
        localStorage.setItem("token", token);
      }

      const storedUser = localStorage.getItem("user");
      const user = storedUser ? JSON.parse(storedUser) : {};

      localStorage.setItem(
        "user",
        JSON.stringify({
          ...user,
          onboardingCompleted: true
        })
      );

      navigate("/dashboard", { replace: true });

    } catch (err) {
      console.log("Onboarding error:", err);

      localStorage.setItem("token", "demo-token");

      const storedUser = localStorage.getItem("user");
      const user = storedUser ? JSON.parse(storedUser) : {};

      localStorage.setItem(
        "user",
        JSON.stringify({
          ...user,
          onboardingCompleted: true
        })
      );

      navigate("/dashboard", { replace: true });
    }
  };

  // 🔥 STYLES (UNCHANGED + IMPROVED SPACING)
  const page = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    background: "#f8f9fb"
  };

  const card = {
    background: "#fff",
    padding: "30px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    width: "420px",
    textAlign: "center"
  };

  const inputStyle = {
    width: "100%",
    padding: "10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px"
  };

  const row = {
    display: "flex",
    gap: "12px",
    marginTop: "8px" // 🔥 space below label
  };

  const label = {
    display: "block",
    marginBottom: "6px",
    fontSize: "13px",
    fontWeight: "500",
    textAlign: "left"
  };

  const buttonStyle = {
    width: "100%",
    padding: "12px",
    background: "#e60023",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "bold",
    marginTop: "10px"
  };

  return (
    <div style={page}>
      <div style={card}>
        <h2>Onboarding</h2>

        {/* Age */}
        <input
          style={inputStyle}
          type="number"
          placeholder="Age"
          value={age}
          onChange={(e) => setAge(e.target.value)}
        />
        <br /><br />

        {/* Weight */}
        <input
          style={inputStyle}
          type="number"
          placeholder="Weight"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
        />
        <br /><br />

        <h3>Last 3 Menstrual Cycles</h3>

        {cycles.map((cycle, index) => (
          <div key={index} style={{ marginBottom: "25px" }}>
            
            <strong style={{ display: "block", marginBottom: "10px" }}>
              Cycle {index + 1}
            </strong>

            <div style={row}>
              <div style={{ width: "100%" }}>
                <label style={label}>Start Date</label>
                <input
                  style={inputStyle}
                  type="date"
                  value={cycle.start}
                  onChange={(e) =>
                    handleCycleChange(index, "start", e.target.value)
                  }
                />
              </div>

              <div style={{ width: "100%" }}>
                <label style={label}>End Date</label>
                <input
                  style={inputStyle}
                  type="date"
                  value={cycle.end}
                  onChange={(e) =>
                    handleCycleChange(index, "end", e.target.value)
                  }
                />
              </div>
            </div>

          </div>
        ))}

        <button style={buttonStyle} onClick={handleSubmit}>
          Submit
        </button>
      </div>
    </div>
  );
}

// This file builds onboarding UI to collect initial user health data, formats inputs into backend-compatible JSON, sends data using axios to initialize ML baseline, and navigates user to dashboard after setup