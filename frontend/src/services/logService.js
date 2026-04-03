import API from "../api/axios";

export const addLog = (data) => API.post("/daily-log", data);
export const getLogs = () => API.get("/daily-log");

// This file manages daily health log API calls by sending user inputs like pain, mood, flow, sleep and retrieving logs from backend, enabling logging functionality used in Logger.jsx and influencing dashboard insights