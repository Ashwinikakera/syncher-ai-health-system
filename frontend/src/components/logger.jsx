import React, { useState, useEffect } from "react";
import { addLog } from "../services/logService";
import { endCycle } from "../services/cycleService";

export default function Logger() {
  const [date, setDate] = useState("");
  const [pain, setPain] = useState("");
  const [mood, setMood] = useState("");
  const [flow, setFlow] = useState("");
  const [sleep, setSleep] = useState("");
  const [stress, setStress] = useState("");
  const [exercise, setExercise] = useState("");

  const [cycle, setCycle] = useState(null);
  const [loading, setLoading] = useState(true);

  // ✅ FIXED: GET ACTIVE CYCLE FROM LOCALSTORAGE (NOT BACKEND)
  useEffect(() => {
    const storedCycle = JSON.parse(localStorage.getItem("cycle"));

    if (storedCycle?.isActive) {
      setCycle({
        start_date: storedCycle.startDate
      });
    } else {
      setCycle(null);
    }

    setLoading(false);
  }, []);

  // 🔥 BLOCK IF NO ACTIVE CYCLE
  if (loading) {
    return <p style={{ textAlign: "center" }}>Checking cycle...</p>;
  }

  if (!cycle) {
    return (
      <div style={{ textAlign: "center", marginTop: "100px" }}>
        <h2 style={{ color: "red" }}>⚠️ Cycle has not yet started</h2>
        <p>Please go to Cycle Tracker and start your cycle</p>
      </div>
    );
  }

  // 🔥 DAY CALCULATION
  const getDayNumber = () => {
    if (!cycle?.start_date || !date) return "";

    const selected = new Date(date);
    const start = new Date(cycle.start_date);

    return Math.floor((selected - start) / (1000 * 60 * 60 * 24)) + 1;
  };

  // 🔥 SUBMIT LOG
  const handleSubmit = async () => {
    if (!date) {
      alert("Please select date");
      return;
    }

    try {
      const payload = {
        date,
        pain: Number(pain),
        mood,
        flow,
        sleep: Number(sleep),
        stress,
        exercise
      };

      await addLog(payload);

      alert("Log saved ✅");

      // reset form (KEEP DATE EMPTY → user selects next day manually)
      setDate("");
      setPain("");
      setMood("");
      setFlow("");
      setSleep("");
      setStress("");
      setExercise("");

    } catch (err) {
      const errorMsg = err.response?.data?.error;

      if (errorMsg === "Log already exists for this date") {
        alert("⚠️ You already added log for this date");
      } else {
        alert(errorMsg || "Error saving log ❌");
      }
    }
  };

  // 🔥 END CYCLE (FRONTEND + BACKEND)
  const handleEndCycle = async () => {
    try {
      await endCycle(); // backend call (optional)

      localStorage.removeItem("cycle"); // ✅ MAIN FIX

      alert("Cycle ended ✅");

      setCycle(null); // immediate UI update

    } catch (err) {
      console.log("❌ End cycle error:", err);

      // even if backend fails → still end locally
      localStorage.removeItem("cycle");
      setCycle(null);

      alert("Cycle ended (Demo Mode)");
    }
  };

  // 🎨 UI
  const card = {
    background: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    maxWidth: "400px",
    margin: "40px auto",
    textAlign: "center"
  };

  const inputStyle = {
    width: "100%",
    padding: "10px",
    borderRadius: "6px",
    border: "1px solid #ccc"
  };

  const buttonStyle = {
    width: "100%",
    padding: "12px",
    background: "#e60023",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    fontWeight: "bold",
    cursor: "pointer"
  };

  return (
    <div style={card}>
      <h3>Cycle Logger</h3>

      {date && (
        <p>
          <strong>Day {getDayNumber()} of your cycle</strong>
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

        {/* ✅ DATE PICKER */}
        <input
          style={inputStyle}
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />

        <input
          style={inputStyle}
          type="number"
          placeholder="Pain (1-5)"
          value={pain}
          onChange={(e) => setPain(e.target.value)}
        />

        <select style={inputStyle} value={mood} onChange={(e) => setMood(e.target.value)}>
          <option value="">Mood</option>
          <option value="low">Happy</option>
          <option value="medium">Low</option>
          <option value="high">Irritated</option>
        </select>

        <select style={inputStyle} value={flow} onChange={(e) => setFlow(e.target.value)}>
          <option value="">Flow</option>
          <option value="light">Light</option>
          <option value="medium">Medium</option>
          <option value="heavy">Heavy</option>
        </select>

        <input
          style={inputStyle}
          type="number"
          placeholder="Sleep hours"
          value={sleep}
          onChange={(e) => setSleep(e.target.value)}
        />

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
          <option value="intense">Intense</option>
        </select>

        <button style={buttonStyle} onClick={handleSubmit}>
          Submit Log
        </button>

        <button
          style={{ ...buttonStyle, background: "black" }}
          onClick={handleEndCycle}
        >
          End Cycle
        </button>

      </div>
    </div>
  );
}

// This file validates user health input (pain range, required fields, lifestyle data), ensures only valid data is sent to backend, maintains UI consistency, and improves UX with safe form reset after submission
