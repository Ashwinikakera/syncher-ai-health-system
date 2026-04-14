import React, { useEffect, useState } from "react";
import { getDashboard } from "../services/dashboardService";
import API from "../api/axios";
import Chart from "../components/chart";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [risk, setRisk] = useState("");
  const [isCorrect, setIsCorrect] = useState("");
  const [noOption, setNoOption] = useState("");
  const [manualDate, setManualDate] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await getDashboard();
      const backendData = res.data || {};

      console.log("FULL RESPONSE:", backendData);

      setRisk(backendData.risk_level || "Low");

      setFeedbackSubmitted(backendData.feedback_submitted || false);

      const today = new Date();
      const formatDate = (date) => date.toISOString().split("T")[0];

      const nextPeriod = new Date(today);
      nextPeriod.setDate(today.getDate() + 28);

      const ovulationStart = new Date(today);
      ovulationStart.setDate(today.getDate() + 14);

      const ovulationEnd = new Date(today);
      ovulationEnd.setDate(today.getDate() + 18);

      const safeData = {
        next_period_date: backendData.next_period || formatDate(nextPeriod),
        ovulation_window: backendData.ovulation_window || [formatDate(ovulationStart), formatDate(ovulationEnd)],
        regularity_score: backendData.regularty_score || 0.75,
        predicted_length: backendData.predicted_length || 28,
        confidence: backendData.confidence || 0.75,
        ai_insights: backendData.ai_insights || "Keep logging daily for better insights",
        recent_symptoms: backendData.recent_symptoms || {},
        medical_history: backendData.medical_history || {}
      };

      setData(safeData);

    } catch (err) {
      console.log(err);
      setData({
        next_period_date: "N/A",
        ovulation_window: ["N/A", "N/A"],
        regularity_score: 0,
        predicted_length: 28,
        confidence: 0,
        ai_insights: "Backend not connected",
        recent_symptoms: {},
        medical_history: {}
      });
      setRisk("Low");
    }
  };

  const handleSubmit = async () => {
    try {
      let payload = null;

      if (isCorrect === "yes") {
        payload = {
          prediction_correct: true,
          actual_date: data.next_period_date,
        };
      }

      if (isCorrect === "no") {
        if (noOption === "other_date") {
          if (!manualDate) { alert("Please select date"); return; }
          payload = {
            prediction_correct: false,
            actual_date: manualDate,
          };
        }

        if (noOption === "not_yet") {
          const today = new Date().toISOString().split("T")[0];
          payload = {
            prediction_correct: false,
            actual_date: today,
          };
        }
      }

      if (!payload) { alert("Please select an option"); return; }

      await API.post("/prediction-feedback/", payload);
      alert("Feedback submitted ✅");

      await fetchDashboard();

      setIsCorrect("");
      setNoOption("");
      setManualDate("");

    } catch (err) {
      console.log("ERROR:", err.response?.data);
      alert(err?.response?.data?.error || "Something went wrong ❌");
    }
  };

  const card = {
    background: "#fff", padding: "25px", borderRadius: "12px",
    boxShadow: "0 6px 18px rgba(0,0,0,0.08)", marginTop: "20px",
    width: "100%", boxSizing: "border-box"
  };

  const inputStyle = {
    width: "100%", padding: "10px", borderRadius: "6px",
    border: "1px solid #ccc", marginTop: "8px"
  };

  const btnStyle = {
    width: "100%", padding: "10px", borderRadius: "6px",
    background: "#e60023", color: "#fff", border: "none",
    marginTop: "8px", cursor: "pointer", fontWeight: "bold"
  };

  return (
    <div style={{ padding: "20px", background: "#ffe5e5", minHeight: "100vh" }}>
      <div style={{ maxWidth: "950px", margin: "0 auto" }}>

        <div style={{
          background: "#ff2d2d", color: "#fff", padding: "12px",
          borderRadius: "8px", marginBottom: "20px",
          fontWeight: "bold", textAlign: "center"
        }}>
          Welcome Back 👋
        </div>

        <h2 style={{ marginBottom: "10px" }}>Dashboard</h2>

        {data ? (
          <>
            <div style={card}>
              <p><strong>Next Period:</strong> {data.next_period_date}</p>
              <p><strong>Predicted Length:</strong> {data.predicted_length} days</p>
              <p><strong>Confidence:</strong> {Math.round(data.confidence * 100)}%</p>
              <p><strong>High Fertility Range:</strong> {data.ovulation_window.join(" to ")}</p>
              <p><strong>Regularity Score:</strong> {data.regularity_score}</p>

              {!feedbackSubmitted ? (
                <div style={{ marginTop: "15px", padding: "12px", background: "#fff5f5", borderRadius: "8px", border: "1px solid #ffcccc" }}>
                  <p><strong>Was this prediction correct?</strong></p>

                  <select style={inputStyle} value={isCorrect}
                    onChange={(e) => {
                      setIsCorrect(e.target.value);
                      setNoOption("");
                      setManualDate("");
                    }}>
                    <option value="">Select...</option>
                    <option value="yes">Yes, it was correct</option>
                    <option value="no">No, it was different</option>
                  </select>

                  {isCorrect === "yes" && (
                    <button style={btnStyle} onClick={handleSubmit}>
                      Submit Feedback
                    </button>
                  )}

                  {isCorrect === "no" && (
                    <>
                      <select style={inputStyle} value={noOption}
                        onChange={(e) => setNoOption(e.target.value)}>
                        <option value="">Select option</option>
                        <option value="other_date">I got it on another date</option>
                        <option value="not_yet">I haven't got my period yet</option>
                      </select>

                      {noOption === "other_date" && (
                        <>
                          <input style={inputStyle} type="date" value={manualDate}
                            onChange={(e) => setManualDate(e.target.value)} />
                          <button style={btnStyle} onClick={handleSubmit}>
                            Submit Feedback
                          </button>
                        </>
                      )}

                      {noOption === "not_yet" && (
                        <button style={btnStyle} onClick={handleSubmit}>
                          Submit Feedback
                        </button>
                      )}
                    </>
                  )}
                </div>
              ) : (
                <div style={{ marginTop: "15px", padding: "12px", background: "#f0fff0", borderRadius: "8px", border: "1px solid #90ee90" }}>
                  <p style={{ color: "green" }}>✅ Prediction feedback submitted. Dashboard will update after your next cycle.</p>
                </div>
              )}

              <h3 style={{ marginTop: "15px" }}>AI Insights:</h3>
              <div style={{ padding: "12px", background: "#f9f9f9", borderRadius: "8px", lineHeight: "1.6", whiteSpace: "pre-wrap", textAlign: "justify" }}>
                {data.ai_insights}
              </div>

              {data.recent_symptoms && Object.keys(data.recent_symptoms).length > 0 && (
                <>
                  <h3>Recent Symptoms:</h3>
                  <p>Pain: {data.recent_symptoms.pain || "N/A"}</p>
                  <p>Mood: {data.recent_symptoms.mood || "N/A"}</p>
                  <p>Flow: {data.recent_symptoms.flow || "N/A"}</p>
                  <p>Stress: {data.recent_symptoms.stress || "N/A"}</p>
                  <p>Sleep: {data.recent_symptoms.sleep || "N/A"} hours</p>
                </>
              )}

              {data.medical_history?.condition && data.medical_history.condition !== "None" && (
                <>
                  <h3>Medical History:</h3>
                  <p>Condition: {data.medical_history.condition}</p>
                  {data.medical_history.notes && <p>Notes: {data.medical_history.notes}</p>}
                </>
              )}
            </div>

            <div style={card}>
              <h3>Health Risk</h3>
              {risk === "High" && <p style={{ color: "red" }}>⚠️ High Risk — Please consult a doctor</p>}
              {risk === "Moderate" && <p style={{ color: "orange" }}>⚠️ Moderate Risk — Exercise + Diet recommended</p>}
              {risk === "Low" && <p style={{ color: "green" }}>✅ Low Risk — You are healthy</p>}
              {risk === "Unknown" && <p style={{ color: "gray" }}>Complete My Health questionnaire for risk assessment</p>}
            </div>

            <div style={card}>
              <h3 style={{ textAlign: "center" }}>Cycle Trend</h3>
              <div style={{ display: "flex", justifyContent: "center" }}>
                <Chart
                  data={[
                    { date: "Day 1", pain: Math.floor(Math.random() * 5) },
                    { date: "Day 2", pain: Math.floor(Math.random() * 5) },
                    { date: "Day 3", pain: Math.floor(Math.random() * 5) },
                    { date: "Day 4", pain: Math.floor(Math.random() * 5) },
                    { date: "Day 5", pain: Math.floor(Math.random() * 5) }
                  ]}
                />
              </div>
            </div>
          </>
        ) : (
          <p>Loading....</p>
        )}
      </div>
    </div>
  );
}
