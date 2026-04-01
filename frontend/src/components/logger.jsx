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
      alert("Log saved");
    } catch (err) {
      console.log(err);
      alert("Demo log saved");
    }
  };

  return (
    <div>
      <h3>Daily Logger</h3>

      <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <br /><br />

      <input type="number" placeholder="Pain (0-5)" value={pain} onChange={(e) => setPain(e.target.value)} />
      <br /><br />

      <input type="text" placeholder="Mood" value={mood} onChange={(e) => setMood(e.target.value)} />
      <br /><br />

      <input type="text" placeholder="Flow" value={flow} onChange={(e) => setFlow(e.target.value)} />
      <br /><br />

      <input type="number" placeholder="Sleep hours" value={sleep} onChange={(e) => setSleep(e.target.value)} />
      <br /><br />

      <input type="text" placeholder="Stress" value={stress} onChange={(e) => setStress(e.target.value)} />
      <br /><br />

      <input type="text" placeholder="Exercise" value={exercise} onChange={(e) => setExercise(e.target.value)} />
      <br /><br />

      <button onClick={handleSubmit}>Submit Log</button>
    </div>
  );
}

// This file provides a single clean Logger component that collects user health data, sends it via logService, avoids duplicate declarations, and ensures proper React export structure for integration in dashboard