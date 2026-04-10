import React, { useState, useEffect } from "react";
import { addCycle, endCycle } from "../services/cycleService";

export default function CycleLogger() {
  const [startDate, setStartDate] = useState("");
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    const cycle = JSON.parse(localStorage.getItem("cycle"));
    if (cycle?.isActive) {
      setIsActive(true);
      setStartDate(cycle.startDate);
    }
  }, []);

  // 🟢 START CYCLE
  const handleStart = async () => {
    if (!startDate) {
      alert("Select start date");
      return;
    }

    try {
      await addCycle({ start_date: startDate });
    } catch (err) {
      console.log("Demo mode");
    }

    localStorage.setItem(
      "cycle",
      JSON.stringify({
        startDate,
        isActive: true
      })
    );

    alert("Cycle started ✅");

    window.location.href = "/daily-logs";
  };

  // 🔴 END CYCLE
  const handleEnd = async () => {
    const today = new Date().toISOString().split("T")[0];

    try {
      await endCycle({ end_date: today });
    } catch (err) {
      console.log("Demo end");
    }

    localStorage.removeItem("cycle");

    alert("Cycle ended ✅");

    window.location.reload();
  };

  // ✅ NEW PAGE BACKGROUND
  const page = {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #ffe5e5, #fff0f0)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center"
  };

  const card = {
    background: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
    maxWidth: "400px",
    width: "100%",
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
    cursor: "pointer",
    fontWeight: "bold"
  };

  const formGroup = {
    display: "flex",
    flexDirection: "column",
    gap: "15px",
    marginTop: "20px"
  };

  return (
    <div style={page}>
      <div style={card}>
        <h3>Cycle Tracker</h3>

        {!isActive ? (
          <div style={formGroup}>
            <input
              style={inputStyle}
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />

            <button style={buttonStyle} onClick={handleStart}>
              Start Cycle
            </button>
          </div>
        ) : (
          <div style={formGroup}>
            <p><strong>Cycle Active from:</strong> {startDate}</p>

            <button
              style={{ ...buttonStyle, background: "black" }}
              onClick={handleEnd}
            >
              End Cycle
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// This component handles cycle tracking by collecting start and end dates and sending them via cycleService, ensuring alignment with API contract while supporting demo fallback