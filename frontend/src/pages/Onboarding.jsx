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

  // ✅ Symptoms
  const [pain, setPain] = useState("");
  const [mood, setMood] = useState("");
  const [flow, setFlow] = useState("");

  // ✅ Medical history
  const [condition, setCondition] = useState("");
  const [otherCondition, setOtherCondition] = useState(""); // used only if "other"

  // ✅ Notes
  const [note, setNote] = useState("");

  const handleCycleChange = (index, field, value) => {
    const updated = [...cycles];
    updated[index][field] = value;
    setCycles(updated);
  };

  // ✅ CLEAR FUNCTION ADDED
  const handleClear = () => {
    setAge("");
    setWeight("");
    setCycles([
      { start: "", end: "" },
      { start: "", end: "" },
      { start: "", end: "" }
    ]);
    setPain("");
    setMood("");
    setFlow("");
    setCondition("");
    setOtherCondition("");
    setNote("");
  };

  const handleSubmit = async () => {
    try {
      // ✅ Pain validation (1–5)
      if (!pain || pain < 1 || pain > 5) {
        alert("Pain must be between 1 and 5");
        return;
      }

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
        cycles: formattedCycles,

        // ✅ NEW DATA
        symptoms: {
          pain: Number(pain),
          mood,
          flow
        },
        medical_history: {
          condition: condition === "other" ? otherCondition : condition
        },
        note
      });

      const storedUser = JSON.parse(localStorage.getItem("user") || "{}");

      localStorage.setItem(
        "user",
        JSON.stringify({
          ...storedUser,
          onboardingCompleted: true
        })
      );

      navigate("/dashboard", { replace: true });

    } catch (err) {
      console.log("Onboarding error:", err);
      navigate("/dashboard", { replace: true });
    }
  };

  // 🎨 UI
  const page = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "200vh",
    background: "#ffe5e5"
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

        <h3>Last 3 Menstrual Cycles (Previous to Oldest)</h3>

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

        <h3>Symptoms</h3>

        <input
          style={inputStyle}
          type="number"
          placeholder="Pain Level (1-5)"
          min="1"
          max="5"
          value={pain}
          onChange={(e) => setPain(e.target.value)}
        />
        <br /><br />

        <select style={inputStyle} value={mood} onChange={(e) => setMood(e.target.value)}>
          <option value="">Mood</option>
          <option value="low">Happy</option>
          <option value="medium">Low</option>
          <option value="high">Irritated</option>
        </select>
        <br /><br />

        <select style={inputStyle} value={flow} onChange={(e) => setFlow(e.target.value)}>
          <option value="">Flow</option>
          <option value="light">Light</option>
          <option value="medium">Medium</option>
          <option value="heavy">Heavy</option>
        </select>
        <br /><br />

        <h3>Medical History</h3>

        <select
          style={inputStyle}
          value={condition}
          onChange={(e) => setCondition(e.target.value)}
        >
          <option value="">Select Condition</option>
          <option value="pcos">PCOS</option>
          <option value="pcod">PCOD</option>
          <option value="uti">UTI (Urinary Tract Infection)</option>
          <option value="thyroid">hyroid</option>
          <option value="none">None</option>
          <option value="other">Other</option>
        </select>
        <br /><br />

        {condition === "other" && (
          <>
            <input
              style={inputStyle}
              type="text"
              placeholder="Enter your condition"
              value={otherCondition}
              onChange={(e) => setOtherCondition(e.target.value)}
            />
            <br /><br />
          </>
        )}

        <textarea
          style={inputStyle}
          placeholder="Any notes (e.g. missed period in last 6 month)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <br /><br />

        <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
          <button
            style={{ ...buttonStyle, width: "50%" }}
            onClick={handleSubmit}
          >
            Submit
          </button>

          <button
            style={{ ...buttonStyle, width: "50%", background: "#555" }}
            onClick={handleClear}
          >
            Clear Form
          </button>
        </div>
      </div>
    </div>
  );
}

// This file builds onboarding UI to collect initial user health data, formats inputs into backend-compatible JSON, sends data using axios to initialize ML baseline, and navigates user to dashboard after setup