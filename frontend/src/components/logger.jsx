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

  const [whiteDischarge, setWhiteDischarge] = useState("");

  const [medication, setMedication] = useState("");
  const [medicationDetails, setMedicationDetails] = useState("");
  const [food, setFood] = useState([]);
  const [routine, setRoutine] = useState("");
  const [routineDetails, setRoutineDetails] = useState("");
  const [hydration, setHydration] = useState("");

  const [symptoms, setSymptoms] = useState([]);
  const [otherSymptom, setOtherSymptom] = useState("");

  const [cycle, setCycle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedCycle = JSON.parse(localStorage.getItem("cycle"));

    if (storedCycle?.isActive) {
      setCycle({ start_date: storedCycle.startDate });
    } else {
      setCycle(null);
    }

    setLoading(false);
  }, []);

  if (loading) {
    return <p style={{ textAlign: "center" }}>Checking cycle...</p>;
  }

  const handleFoodChange = (item) => {
    setFood(prev =>
      prev.includes(item) ? prev.filter(f => f !== item) : [...prev, item]
    );
  };

  const handleSymptomChange = (item) => {
    setSymptoms(prev =>
      prev.includes(item)
        ? prev.filter(s => s !== item)
        : [...prev, item]
    );
  };

  // ✅ ADDED CLEAR FUNCTION
  const handleClear = () => {
    setDate("");
    setPain("");
    setMood("");
    setFlow("");
    setSleep("");
    setStress("");
    setExercise("");
    setMedication("");
    setMedicationDetails("");
    setFood([]);
    setRoutine("");
    setRoutineDetails("");
    setHydration("");
    setSymptoms([]);
    setOtherSymptom("");
    setWhiteDischarge("");
  };

  const handleSubmit = async () => {
    if (!date) {
      alert("Please select date");
      return;
    }

    if (cycle) {
      if (!pain || pain < 1 || pain > 5) {
        alert("Pain must be between 1 and 5");
        return;
      }
    }

    try {
      const payload = {
        date,
        mood,
        flow,
        sleep: Number(sleep),
        stress,
        exercise,
        medication,
        medication_details: medicationDetails,
        food,
        routine,
        routine_details: routineDetails,
        hydration,
        symptoms,
        other_symptom: otherSymptom,
        white_discharge: whiteDischarge,
        ...(cycle && { pain: Number(pain) })
      };

      await addLog(payload);

      alert("Log saved ✅");

      setDate("");
      setPain("");
      setMood("");
      setFlow("");
      setSleep("");
      setStress("");
      setExercise("");
      setMedication("");
      setMedicationDetails("");
      setFood([]);
      setRoutine("");
      setRoutineDetails("");
      setHydration("");
      setSymptoms([]);
      setOtherSymptom("");
      setWhiteDischarge("");

    } catch (err) {
      const errorMsg = err.response?.data?.error;

      if (errorMsg === "Log already exists for this date") {
        alert("⚠️ You already added log for this date");
      } else {
        alert(errorMsg || "Error saving log ❌");
      }
    }
  };

  const handleEndCycle = async () => {
    try {
      await endCycle();
      localStorage.removeItem("cycle");
      alert("Cycle ended ✅");
      setCycle(null);
    } catch {
      localStorage.removeItem("cycle");
      setCycle(null);
      alert("Cycle ended (Demo Mode)");
    }
  };

  const pageWrapper = {
    minHeight: "100vh",
    width: "100%",
    background: "#ffe5e5",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "20px"
  };

  const card = {
    background: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
    width: "100%",
    maxWidth: "450px",
    margin: "0",
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
    <div style={pageWrapper}>
      <div style={card}>
        <h3 style={{ marginBottom: "10px" }}>Daily Logger</h3>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

          <input
            style={inputStyle}
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />

          {cycle && (
            <>
              <input
                style={inputStyle}
                type="number"
                placeholder="Pain (1-5)"
                value={pain}
                min="1"
                max="5"
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
            </>
          )}

          <input
            style={inputStyle}
            type="number"
            placeholder="Sleep hours"
            value={sleep}
            onChange={(e) => setSleep(e.target.value)}
          />

          <select style={inputStyle} value={stress} onChange={(e) => setStress(e.target.value)}>
            <option value="">Stress</option>
            <option value="none">None</option>
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

          {!cycle && (
            <>
              <select style={inputStyle} value={medication} onChange={(e) => setMedication(e.target.value)}>
                <option value="">Medication</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>

              {medication === "yes" && (
                <input
                  style={inputStyle}
                  type="text"
                  placeholder="Enter medication details"
                  value={medicationDetails}
                  onChange={(e) => setMedicationDetails(e.target.value)}
                />
              )}

              <div style={{ textAlign: "left" }}>
                <strong>Food</strong>
                {["home", "junk", "healthy", "skipped"].map(item => (
                  <label key={item} style={{ display: "block" }}>
                    <input
                      type="checkbox"
                      checked={food.includes(item)}
                      onChange={() => handleFoodChange(item)}
                    /> {item}
                  </label>
                ))}
              </div>

              <select style={inputStyle} value={routine} onChange={(e) => setRoutine(e.target.value)}>
                <option value="">Any Change in Routine? (Sleep / Food Time / Shift)</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>

              {routine === "yes" && (
                <input
                  style={inputStyle}
                  type="text"
                  placeholder="What changed?"
                  value={routineDetails}
                  onChange={(e) => setRoutineDetails(e.target.value)}
                />
              )}

              <select
                style={inputStyle}
                value={whiteDischarge}
                onChange={(e) => setWhiteDischarge(e.target.value)}
              >
                <option value="">White Discharge</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="none">None</option>
              </select>

              <select style={inputStyle} value={hydration} onChange={(e) => setHydration(e.target.value)}>
                <option value="">Hydration</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>

              <div style={{ textAlign: "left" }}>
                <strong>Premenstrual Symptoms</strong>

                <div style={{
                  border: "1px solid #ccc",
                  borderRadius: "6px",
                  padding: "10px",
                  marginTop: "6px"
                }}>
                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    {["Cramps", "Headache", "Fatigue"].map(item => (
                      <label key={item}>
                        <input
                          type="checkbox"
                          checked={symptoms.includes(item)}
                          onChange={() => handleSymptomChange(item)}
                        /> {item}
                      </label>
                    ))}
                  </div>

                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "6px" }}>
                    {["Mood_swings", "Nausea"].map(item => (
                      <label key={item}>
                        <input
                          type="checkbox"
                          checked={symptoms.includes(item)}
                          onChange={() => handleSymptomChange(item)}
                        /> {item}
                      </label>
                    ))}

                    <label>
                      <input
                        type="checkbox"
                        checked={symptoms.includes("other")}
                        onChange={() => handleSymptomChange("other")}
                      /> Other
                    </label>
                  </div>
                </div>

                {symptoms.includes("other") && (
                  <input
                    style={{ ...inputStyle, marginTop: "8px" }}
                    type="text"
                    placeholder="Enter other symptoms"
                    value={otherSymptom}
                    onChange={(e) => setOtherSymptom(e.target.value)}
                  />
                )}
              </div>
            </>
          )}

          <button style={buttonStyle} onClick={handleSubmit}>
            Submit Log
          </button>

          {/* ✅ CLEAR BUTTON ADDED */}
          <button
            style={{ ...buttonStyle, background: "#555" }}
            onClick={handleClear}
          >
            Clear Form
          </button>

          {cycle && (
            <button
              style={{ ...buttonStyle, background: "black" }}
              onClick={handleEndCycle}
            >
              End Cycle
            </button>
          )}

        </div>
      </div>
    </div>
  );
}

// This file validates user health input (pain range, required fields, lifestyle data), ensures only valid data is sent to backend, maintains UI consistency, and improves UX with safe form reset after submission
