import React, { useState, useEffect } from "react";
import API from "../api/axios";

import imgA from "../images/A.png";
import imgB from "../images/B.png";
import imgC from "../images/C.png";

export default function MyHealth() {
  const [form, setForm] = useState({
    q1: "", q2: "", q3: "", q4: "", q5: "",
    q6: "", q7: "", q8: "", q9: "", q10: ""
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [openSection, setOpenSection] = useState(null);
  const [errors, setErrors] = useState({});

  const toggleSection = (section) => {
    setOpenSection(prev => (prev === section ? null : section));
  };

  const handleChange = (q, value) => {
    setForm(prev => ({ ...prev, [q]: value }));
  };

  const handleClear = () => {
    setForm({ q1: "", q2: "", q3: "", q4: "", q5: "", q6: "", q7: "", q8: "", q9: "", q10: "" });
    setErrors({});
    setResult(null);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await API.get("/my-health/");
        if (res.data?.responses) {
          setForm(res.data.responses);
          setResult(res.data);
        }
      } catch {}
      finally { setLoading(false); }
    };
    fetchData();
  }, []);

  const handleSubmit = async () => {
    let newErrors = {};
    let firstErrorKey = null;

    Object.entries(form).forEach(([key, value]) => {
      if (!value) {
        newErrors[key] = "This field is required";
        if (!firstErrorKey) firstErrorKey = key;
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      if (newErrors.q1 || newErrors.q2 || newErrors.q3) setOpenSection("A");
      else if (newErrors.q4 || newErrors.q5 || newErrors.q6 || newErrors.q7 || newErrors.q8) setOpenSection("B");
      else setOpenSection("C");
      setTimeout(() => {
        const el = document.querySelector(`[name="${firstErrorKey}"]`);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
      return;
    }

    setErrors({});

    try {
      setSubmitting(true);

      // POST to save
      await API.post("/my-health/", form);

      // GET to fetch score + AI analysis
      const getRes = await API.get("/my-health/");
      setResult(getRes.data);

      setTimeout(() => {
        const el = document.getElementById("result-section");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 200);

    } catch (err) {
      console.error("API ERROR:", err?.response?.data || err.message);
      alert(
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        "Something went wrong ❌"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const getScoreColor = (score) => {
    if (score < 40) return "#28a745";
    if (score < 70) return "#ffc107";
    return "#dc3545";
  };

  const page = {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #ffe5e5, #fff0f5)",
    display: "flex", justifyContent: "center", alignItems: "center", padding: "20px"
  };

  const card = {
    background: "#fff", padding: "30px", borderRadius: "16px",
    width: "900px", boxShadow: "0 10px 30px rgba(0,0,0,0.1)"
  };

  const accordionCard = {
    marginTop: "20px", borderRadius: "12px",
    boxShadow: "0 5px 15px rgba(0,0,0,0.08)", padding: "15px"
  };

  const headingRow = {
    display: "flex", flexDirection: "column", alignItems: "center",
    textAlign: "center", gap: "10px", cursor: "pointer"
  };

  const imageStyle = {
    width: "420px", height: "auto", objectFit: "contain", borderRadius: "10px"
  };

  const input = (q) => ({
    width: "100%",
    padding: "18px",
    marginTop: "12px",
    borderRadius: "10px",
    fontSize: "18px",
    fontWeight: "500",

    // 🎯 NEW LOGIC
    background: errors[q]
      ? "#ffe6e6"                     // error (light red)
      : form[q]
      ? "#e6fff2"                     // answered (light green)
      : "#fafafa",                    // default

    border: errors[q]
      ? "2px solid red"
      : form[q]
      ? "2px solid #28a745"           // green border when answered
      : "1px solid #ccc",

    outline: "none",
    transition: "all 0.3s ease"
  });
  


  const fadeStyle = `
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;

  if (loading) return <p style={{ textAlign: "center" }}>Loading...</p>;

  return (
    <div style={page}>
      <style>{fadeStyle}</style>

      <div style={card}>
        <h2 style={{ textAlign: "center" }}>My Health Analysis 🧠</h2>

        {/* A — Hyperandrogenism */}
        <div style={accordionCard}>
          <div style={headingRow} onClick={() => toggleSection("A")}>
            <img src={imgA} style={imageStyle} alt="A" />
            <h4 style={{ fontSize: "20px", fontWeight: "700" }}>A. Hyperandrogenism</h4>
          </div>

          {openSection === "A" && (
            <>
              <select name="q1" style={input("q1")} value={form.q1}
                onChange={(e) => { handleChange("q1", e.target.value); setErrors(p => ({ ...p, q1: "" })); }}>
                <option value="">Acne severity (especially jawline/chin)?</option>
                <option>None</option>
                <option>Mild/Occasional</option>
                <option>Persistent/Recurrent</option>
                <option>Severe/Cystic</option>
              </select>
              {errors.q1 && <p style={{ color: "red" }}>{errors.q1}</p>}

              <select name="q2" style={input("q2")} value={form.q2}
                onChange={(e) => { handleChange("q2", e.target.value); setErrors(p => ({ ...p, q2: "" })); }}>
                <option value="">Excess facial/body hair (chin, upper lip, chest)?</option>
                <option>None</option>
                <option>Mild</option>
                <option>Moderate</option>
                <option>Significant</option>
              </select>
              {errors.q2 && <p style={{ color: "red" }}>{errors.q2}</p>}

              <select name="q3" style={input("q3")} value={form.q3}
                onChange={(e) => { handleChange("q3", e.target.value); setErrors(p => ({ ...p, q3: "" })); }}>
                <option value="">Hair thinning or hair fall (crown/front)?</option>
                <option>No</option>
                <option>Mild</option>
                <option>Noticeable</option>
              </select>
              {errors.q3 && <p style={{ color: "red" }}>{errors.q3}</p>}
            </>
          )}
        </div>

        {/* B — Metabolic Indicators */}
        <div style={accordionCard}>
          <div style={headingRow} onClick={() => toggleSection("B")}>
            <img src={imgB} style={imageStyle} alt="B" />
            <h4>B. Metabolic Indicators</h4>
          </div>

          {openSection === "B" && (
            <>
              <select name="q4" style={input("q4")} value={form.q4}
                onChange={(e) => { handleChange("q4", e.target.value); setErrors(p => ({ ...p, q4: "" })); }}>
                <option value="">Unexplained weight gain in last 6-12 months?</option>
                <option>No</option>
                <option value="Mild (2-4 kg)">Mild (2-4 kg)</option>
                <option value="Moderate (5-8 kg)">Moderate (5-8 kg)</option>
                <option value="Significant (>8 kg)">Significant (&gt;8 kg)</option>
              </select>
              {errors.q4 && <p style={{ color: "red" }}>{errors.q4}</p>}

              <select name="q5" style={input("q5")} value={form.q5}
                onChange={(e) => { handleChange("q5", e.target.value); setErrors(p => ({ ...p, q5: "" })); }}>
                <option value="">Unexplained weight loss in last 6-12 months?</option>
                <option>No</option>
                <option value="Mild (2-4 kg)">Mild (2-4 kg)</option>
                <option value="Moderate (5-8 kg)">Moderate (5-8 kg)</option>
                <option value="Significant (>8 kg)">Significant (&gt;8 kg)</option>
              </select>
              {errors.q5 && <p style={{ color: "red" }}>{errors.q5}</p>}

              <select name="q6" style={input("q6")} value={form.q6}
                onChange={(e) => { handleChange("q6", e.target.value); setErrors(p => ({ ...p, q6: "" })); }}>
                <option value="">Fat distribution mainly around abdomen?</option>
                <option>No</option>
                <option>Yes</option>
              </select>
              {errors.q6 && <p style={{ color: "red" }}>{errors.q6}</p>}

              <select name="q7" style={input("q7")} value={form.q7}
                onChange={(e) => { handleChange("q7", e.target.value); setErrors(p => ({ ...p, q7: "" })); }}>
                <option value="">Dark patches on neck/armpits?</option>
                <option>No</option>
                <option>Mild</option>
                <option>Clear/Visible</option>
              </select>
              {errors.q7 && <p style={{ color: "red" }}>{errors.q7}</p>}

              <select name="q8" style={input("q8")} value={form.q8}
                onChange={(e) => { handleChange("q8", e.target.value); setErrors(p => ({ ...p, q8: "" })); }}>
                <option value="">Energy after meals (especially carbs)?</option>
                <option>Normal</option>
                <option>Slight Sleepiness</option>
                <option value="Strong fatigue/crashes">Strong fatigue/crashes</option>
              </select>
              {errors.q8 && <p style={{ color: "red" }}>{errors.q8}</p>}
            </>
          )}
        </div>

        {/* C — Lifestyle */}
        <div style={accordionCard}>
          <div style={headingRow} onClick={() => toggleSection("C")}>
            <img src={imgC} style={imageStyle} alt="C" />
            <h4>C. Lifestyle &amp; Behavior</h4>
          </div>

          {openSection === "C" && (
            <>
              <select name="q9" style={input("q9")} value={form.q9}
                onChange={(e) => { handleChange("q9", e.target.value); setErrors(p => ({ ...p, q9: "" })); }}>
                <option value="">Physical activity level?</option>
                <option value=">=4 times/week">≥4 times/week</option>
                <option value="2-3 times/week">2-3 times/week</option>
                <option value="Rare/none">Rare/none</option>
              </select>
              {errors.q9 && <p style={{ color: "red" }}>{errors.q9}</p>}

              <select name="q10" style={input("q10")} value={form.q10}
                onChange={(e) => { handleChange("q10", e.target.value); setErrors(p => ({ ...p, q10: "" })); }}>
                <option value="">Diet pattern?</option>
                <option>Mostly whole foods</option>
                <option>Mixed</option>
                <option>High sugar/processed/junk</option>
              </select>
              {errors.q10 && <p style={{ color: "red" }}>{errors.q10}</p>}
            </>
          )}
        </div>

        {/* BUTTONS */}
        <div style={{ display: "flex", gap: "10px", marginTop: "15px" }}>
          <button
            style={{
              flex: 1, padding: "14px",
              background: submitting ? "#999" : "#e60023",
              color: "#fff", borderRadius: "10px", fontWeight: "600",
              cursor: submitting ? "not-allowed" : "pointer", border: "none"
            }}
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Analyzing... ⏳" : "Analyze 🔍"}
          </button>

          <button
            style={{ flex: 1, padding: "12px", background: "#555", color: "#fff", border: "none", borderRadius: "10px", cursor: "pointer" }}
            onClick={handleClear}
          >
            Clear
          </button>
        </div>

        {/* RESULT */}
        {result && (
          <div
            id="result-section"
            style={{
              marginTop: "25px", padding: "20px", borderRadius: "14px",
              background: "#fff", boxShadow: "0 6px 20px rgba(0,0,0,0.1)",
              animation: "fadeIn 0.5s ease"
            }}
          >
            <h3>🧾 Health Analysis Result</h3>

            <div style={{ marginTop: "15px" }}>
              <strong>Health Risk Score:</strong>
              <div style={{ marginTop: "8px", height: "12px", width: "100%", background: "#eee", borderRadius: "10px", overflow: "hidden" }}>
                <div style={{
                  height: "100%", width: `${result.score}%`,
                  background: getScoreColor(result.score), transition: "width 0.7s ease"
                }} />
              </div>
              <p style={{ marginTop: "5px", fontWeight: "600" }}>{result.score}%</p>
            </div>

            <p>
              <strong>Risk Level:</strong>{" "}
              <span style={{
                padding: "6px 12px", borderRadius: "8px", fontWeight: "600",
                background: result.risk_level === "Low" ? "#d4edda" : result.risk_level === "Moderate" ? "#fff3cd" : "#f8d7da",
                color: result.risk_level === "Low" ? "green" : result.risk_level === "Moderate" ? "#856404" : "red"
              }}>
                {result.risk_level}
              </span>
            </p>

            {result.ai_analysis && (
              <div style={{ marginTop: "15px", padding: "12px", background: "#f9f9f9", borderRadius: "8px", lineHeight: "1.6" }}>
                <strong>AI Analysis:</strong>
                <p style={{ marginTop: "8px", whiteSpace: "pre-wrap", textAlign: "justify" }}>
                  {result.ai_analysis}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
