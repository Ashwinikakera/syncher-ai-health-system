import API from "../api/axios";

export const addCycle = (data) => API.post("/cycle", data);
export const getCycles = () => API.get("/cycle");

// This file handles cycle-related API calls by sending period start/end data and fetching cycle history from backend using axios instance, enabling cycle tracking features used in Logger.jsx and Dashboard.jsx