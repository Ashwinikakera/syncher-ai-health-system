import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";

export default function Onboarding() {
  const [age, setAge] = useState("");
  const [weight, setWeight] = useState("");
  const [cycleHistory, setCycleHistory] = useState("");
  const [avgCycleLength, setAvgCycleLength] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async () => {
    try {
      const formattedHistory = cycleHistory.split(",");

      await API.post("/onboarding", {
        age: Number(age),
        weight: Number(weight),
        cycle_history: formattedHistory,
        avg_cycle_length: Number(avgCycleLength)
      });

      alert("Onboarding completed");
      navigate("/dashboard");
    } catch (err) {
      console.log(err);
      alert("Onboarding failed (backend not connected yet)");
    }
  };

  return (
    <div>
      <h2>Onboarding</h2>

      <input
        type="number"
        placeholder="Age"
        value={age}
        onChange={(e) => setAge(e.target.value)}
      />
      <br /><br />

      <input
        type="number"
        placeholder="Weight"
        value={weight}
        onChange={(e) => setWeight(e.target.value)}
      />
      <br /><br />

      <input
        type="text"
        placeholder="Cycle history (comma separated dates)"
        value={cycleHistory}
        onChange={(e) => setCycleHistory(e.target.value)}
      />
      <br /><br />

      <input
        type="number"
        placeholder="Avg cycle length"
        value={avgCycleLength}
        onChange={(e) => setAvgCycleLength(e.target.value)}
      />
      <br /><br />

      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}

// This file builds onboarding UI to collect initial user health data, formats inputs into backend-compatible JSON, sends data using axios to initialize ML baseline, and navigates user to dashboard after setup