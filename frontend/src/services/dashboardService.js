import API from "../api/axios";

export const getDashboard = () => API.get("/dashboard");

// This file fetches dashboard data from backend including predictions, ovulation window, insights and scores using axios, enabling Dashboard.jsx to display analytics and ML-generated health insights