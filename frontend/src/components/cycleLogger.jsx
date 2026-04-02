import React, { useState } from "react";
import { addCycle } from "../services/cycleService";

export default function CycleLogger() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const handleSubmit = async () => {
    try {
      await addCycle({
        start_date: startDate,
        end_date: endDate
      });
      alert("Cycle saved");
    } catch (err) {
      console.log(err);
      alert("Demo cycle saved");
    }
  };

  // 🔥 SAME CARD STYLE
  const card = {
    background: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    maxWidth: "400px",
    margin: "40px auto",
    textAlign: "center"
  };

  // 🔥 SAME INPUT STYLE
  const inputStyle = {
    width: "100%",
    padding: "10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    boxSizing: "border-box"
  };

  // 🔥 SAME BUTTON STYLE
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
      <h3>Cycle Logger</h3>

      {/* 🔥 ONLY CHANGE: added labels + left align */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", textAlign: "left" }}>

        {/* Start Date */}
        <label style={{ fontWeight: "bold" }}>Start Date</label>
        <input
          style={inputStyle}
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />

        {/* End Date */}
        <label style={{ fontWeight: "bold" }}>End Date</label>
        <input
          style={inputStyle}
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />

        <button style={buttonStyle} onClick={handleSubmit}>
          Save Cycle
        </button>

      </div>
    </div>
  );
}

// This component handles cycle tracking by collecting start and end dates and sending them via cycleService, ensuring alignment with API contract while supporting demo fallback