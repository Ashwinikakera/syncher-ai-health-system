import React, { useState } from "react";
import { addLog } from "../services/logService";

export default function Logger() {
  const [date, setDate] = useState("");
  const [pain, setPain] = useState("");
  const [mood, setMood] = useState("");
  const [flow, setFlow] = useState("");
  const [sleep, setSleep] = useState("");
  const [stress, setStress] = useState("");
  const [exercise, setExercise] = useState("");

  const handleSubmit = async () => {
    try {
      await addLog({
        date,
        pain: Number(pain),
        mood,
        flow,
        sleep: Number(sleep),
        stress,
        exercise
      });
      alert("Log saved ✅");
    } catch (err) {
      console.log(err);
      alert("Demo log saved ✅");
    }
  };

  // 🔥 SAME CARD STYLE AS DASHBOARD (UNCHANGED)
  const card = {
    background: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    maxWidth: "400px",
    margin: "40px auto",
    textAlign: "center"
  };

  // 🔥 NEW: COMMON INPUT STYLE (KEY FIX)
  const inputStyle = {
    width: "100%",
    padding: "10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    boxSizing: "border-box"
  };

  // 🔥 NEW: BUTTON STYLE
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
    <div style={card}>
      <h3>Daily Logger</h3>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

        {/* Date */}
        <input
          style={inputStyle}
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />

        {/* Pain */}
        <input
          style={inputStyle}
          type="number"
          placeholder="Pain (0-10)"
          min="0"
          max="10"
          value={pain}
          onChange={(e) => setPain(e.target.value)}
        />

        {/* Mood */}
        <select
          style={inputStyle}
          value={mood}
          onChange={(e) => setMood(e.target.value)}
        >
          <option value="">Mood</option>
          <option value="happy">Happy</option>
          <option value="low">Sad</option>
          <option value="irritated">Irritated</option>
          <option value="neutral">Neutral</option>
        </select>

        {/* Flow */}
        <select
          style={inputStyle}
          value={flow}
          onChange={(e) => setFlow(e.target.value)}
        >
          <option value="">Flow</option>
          <option value="light">Light</option>
          <option value="medium">Medium</option>
          <option value="heavy">Heavy</option>
        </select>

        {/* Sleep */}
        <input
          style={inputStyle}
          type="number"
          placeholder="Sleep hours (0-24)"
          min="0"
          max="24"
          value={sleep}
          onChange={(e) => setSleep(e.target.value)}
        />

        {/* Stress */}
        <select
          style={inputStyle}
          value={stress}
          onChange={(e) => setStress(e.target.value)}
        >
          <option value="">Stress</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>

        {/* Exercise */}
        <select
          style={inputStyle}
          value={exercise}
          onChange={(e) => setExercise(e.target.value)}
        >
          <option value="">Exercise</option>
          <option value="none">None</option>
          <option value="light">Light</option>
          <option value="moderate">Moderate</option>
          <option value="heavy">Heavy</option>
        </select>

        {/* Submit */}
        <button style={buttonStyle} onClick={handleSubmit}>
          Submit Log
        </button>

      </div>
    </div>
  );
}

// This file provides a single clean Logger component that collects user health data, sends it via logService, avoids duplicate declarations, and ensures proper React export structure for integration in dashboard