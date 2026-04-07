import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";
import { addCycle } from "../services/cycleService";

export default function Onboarding() {
  const navigate = useNavigate();

  const [age, setAge] = useState("");
  const [weight, setWeight] = useState("");

  // ✅ FIX: added missing state
  const [selectedDate, setSelectedDate] = useState("");

  const [cycles, setCycles] = useState([
    { start: "", end: "" },
    { start: "", end: "" },
    { start: "", end: "" }
  ]);

  // ✅ FIXED FUNCTION
  const handleStartCycle = async () => {
    if (!selectedDate) {
      alert("Please select start date");
      return;
    }

    try {
      await addCycle({
        start_date: selectedDate
      });

      alert("Cycle started ✅");

    } catch (err) {
      console.log("❌ Cycle start error:", err);
    }
  };

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

      const cycle_history = cycles
        .map((c) => c.start)
        .filter(Boolean);

      let avg_cycle_length = 28;

      if (cycle_history.length >= 2) {
        const diffs = [];

        for (let i = 1; i < cycle_history.length; i++) {
          const d1 = new Date(cycle_history[i - 1]);
          const d2 = new Date(cycle_history[i]);

          const diff = (d2 - d1) / (1000 * 60 * 60 * 24);

          if (!isNaN(diff)) diffs.push(diff);
        }

        if (diffs.length > 0) {
          avg_cycle_length =
            diffs.reduce((a, b) => a + b, 0) / diffs.length;
        }
      }

      await API.post("/onboarding/", {
        age: Number(age),
        weight: Number(weight),
        cycle_history,
        avg_cycle_length: Math.round(avg_cycle_length),
        cycles: formattedCycles
      });

      const token = localStorage.getItem("token");

      if (!token) {
        navigate("/login");
        return;
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

  // 🎨 UI (UNCHANGED)
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
    marginTop: "8px"
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

        <input
          style={inputStyle}
          type="number"
          placeholder="Age"
          value={age}
          onChange={(e) => setAge(e.target.value)}
        />
        <br /><br />

        <input
          style={inputStyle}
          type="number"
          placeholder="Weight"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
        />
        <br /><br />

        {/* 🔥 NEW: START CYCLE */}
        <h3>Start Current Cycle</h3>

        <input
          style={inputStyle}
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />

        <button style={buttonStyle} onClick={handleStartCycle}>
          Start Cycle
        </button>

        <h3>Last 3 Menstrual Cycles</h3>

        {cycles.map((cycle, index) => (
          <div key={index} style={{ marginBottom: "25px" }}>
            <strong>Cycle {index + 1}</strong>

            <div style={row}>
              <input
                style={inputStyle}
                type="date"
                value={cycle.start}
                onChange={(e) =>
                  handleCycleChange(index, "start", e.target.value)
                }
              />
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
        ))}

        <button style={buttonStyle} onClick={handleSubmit}>
          Submit
        </button>
      </div>
    </div>
  );
}

// This file builds onboarding UI to collect initial user health data, formats inputs into backend-compatible JSON, sends data using axios to initialize ML baseline, and navigates user to dashboard after setup