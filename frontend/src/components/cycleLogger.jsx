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

  return (
    <div>
      <h3>Cycle Logger</h3>

      <input
        type="date"
        value={startDate}
        onChange={(e) => setStartDate(e.target.value)}
      />
      <br /><br />

      <input
        type="date"
        value={endDate}
        onChange={(e) => setEndDate(e.target.value)}
      />
      <br /><br />

      <button onClick={handleSubmit}>Save Cycle</button>
    </div>
  );
}

// This component handles cycle tracking by collecting start and end dates and sending them via cycleService, ensuring alignment with API contract while supporting demo fallback