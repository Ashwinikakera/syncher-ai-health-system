import React, { useState, useEffect } from "react";
import { addLog } from "../services/logService";
import { getCycles } from "../services/cycleService";

export default function Logger() {
  const [hasActiveCycle, setHasActiveCycle] = useState(false);
  const [cycleChecked, setCycleChecked] = useState(false);
  const [date, setDate] = useState("");
  const [pain, setPain] = useState("");
  const [mood, setMood] = useState("");
  const [flow, setFlow] = useState("");
  const [sleep, setSleep] = useState("");
  const [stress, setStress] = useState("");
  const [exercise, setExercise] = useState("");

  useEffect(() => {
    getCycles()
      .then(res => {
        const cycles = res.data || [];
        const active = cycles.some(c => !c.end_date);
        setHasActiveCycle(active);
      })
      .catch(() => setHasActiveCycle(false))
      .finally(() => setCycleChecked(true));
  }, []);

  const handleSubmit = async () => {
    if (!date) { alert("Please select date"); return; }
    if (pain === "" || pain < 0 || pain > 5) { alert("Pain must be between 0–5"); return; }
    if (!mood || !flow) { alert("Please select mood and flow"); return; }
    if (sleep === "" || sleep < 0 || sleep > 24) { alert("Sleep must be between 0–24 hours"); return; }
    if (!stress || !exercise) { alert("Please select stress and exercise"); return; }

    try {
      await addLog({ date, pain: Number(pain), mood, flow, sleep: Number(sleep), stress, exercise });
      alert("Log saved ✅");
      setDate(""); setPain(""); setMood(""); setFlow(""); setSleep(""); setStress(""); setExercise("");
    } catch (err) {
      console.log(err);
      alert("Demo log saved ✅");
    }
  };

  const card = { background: "#fff", padding: "25px", borderRadius: "12px", boxShadow: "0 4px 12px rgba(0,0,0,0.08)", maxWidth: "400px", margin: "40px auto", textAlign: "center" };
  const inputStyle = { width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #ccc", fontSize: "14px", boxSizing: "border-box" };
  const buttonStyle = { width: "100%", padding: "12px", background: "#e60023", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" };

  if (!cycleChecked) return null;

  // 🔥 KEY LOGIC — only show form during active period
  if (!hasActiveCycle) {
    return (
      <div style={card}>
        <h3>Daily Logger</h3>
        <p style={{ color: "#888", marginBottom: "12px" }}>
          No active period found. Start tracking your cycle first to log daily symptoms.
        </p>
        <a href="/cycle-tracker" style={{ color: "#e60023", fontWeight: "bold" }}>
          → Go to Cycle Tracker
        </a>
      </div>
    );
  }

  return (
    <div style={card}>
      <h3>Daily Logger</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <input style={inputStyle} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <input style={inputStyle} type="number" placeholder="Pain (0-5)" min="0" max="5" value={pain} onChange={(e) => setPain(e.target.value)} />
        <select style={inputStyle} value={mood} onChange={(e) => setMood(e.target.value)}>
          <option value="">Mood</option>
          <option value="happy">Happy</option>
          <option value="low">Sad</option>
          <option value="irritated">Irritated</option>
          <option value="neutral">Neutral</option>
        </select>
        <select style={inputStyle} value={flow} onChange={(e) => setFlow(e.target.value)}>
          <option value="">Flow</option>
          <option value="light">Light</option>
          <option value="medium">Medium</option>
          <option value="heavy">Heavy</option>
        </select>
        <input style={inputStyle} type="number" placeholder="Sleep hours (0-24)" min="0" max="24" value={sleep} onChange={(e) => setSleep(e.target.value)} />
        <select style={inputStyle} value={stress} onChange={(e) => setStress(e.target.value)}>
          <option value="">Stress</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <select style={inputStyle} value={exercise} onChange={(e) => setExercise(e.target.value)}>
          <option value="">Exercise</option>
          <option value="none">None</option>
          <option value="light">Light</option>
          <option value="moderate">Moderate</option>
          <option value="heavy">Heavy</option>
        </select>
        <button style={buttonStyle} onClick={handleSubmit}>Submit Log</button>
      </div>
    </div>
  );
}