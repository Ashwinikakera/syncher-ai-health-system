import React, { useEffect, useState } from "react";
import { getDashboard } from "../services/dashboardService";

import Chart from "../components/chart";
import Chatbot from "../components/chatbot";
import Logger from "../components/logger";

export default function Dashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await getDashboard();
      setData(res.data);
    } catch (err) {
      console.log(err);
      setData({
        next_period_date: "N/A",
        ovulation_window: ["N/A", "N/A"],
        cycle_regularity_score: 0,
        insights: ["Backend not connected"]
      });
    }
  };

  const card = {
  background: "#fff",
  padding: "15px",
  borderRadius: "12px",
  boxShadow: "0 4px 12px rgba(0,0,0,0.08)"
};

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
  gap: "20px"
};


  return (
    <div style={{ padding: "20px" }}>
      <h2>Dashboard</h2>

      {data ? (
        <div>
          <p><strong>Next Period:</strong> {data.next_period_date}</p>

          <p>
            <strong>Ovulation Window:</strong>{" "}
            {data.ovulation_window.join(" to ")}
          </p>

          <p>
            <strong>Regularity Score:</strong>{" "}
            {data.cycle_regularity_score}
          </p>

          <h3>Insights:</h3>
          <ul>
            {data.insights.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>

          {/* Chart Section */}
          <Chart
            data={[
              { date: "Day 1", pain: 2 },
              { date: "Day 2", pain: 4 },
              { date: "Day 3", pain: 1 }
            ]}
          />

          {/* Logger Section */}
          <Logger />

          {/* Chatbot Section */}
          <Chatbot />
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

// This file fetches dashboard data from backend, displays predictions and insights, integrates chart visualization, daily logger, and chatbot components, and ensures complete user interaction flow even with fallback mock data