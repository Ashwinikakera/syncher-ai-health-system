import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function Chart({ data }) {
  return (
    <div>
      <h3>Cycle Trend</h3>

      <LineChart width={400} height={250} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="pain" />
      </LineChart>
    </div>
  );
}

// This file renders a line chart using recharts to visualize user health trends like pain over time, receives processed data as props from Dashboard.jsx, and enhances analytical understanding of cycle patterns through graphical representation