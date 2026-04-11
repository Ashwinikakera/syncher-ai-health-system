import API from "../api/axios";

//  URL /cycle/start
export const addCycle = (data) => API.post("/cycle/start/", data);
export const getCycles = () => API.get("/cycle/");

// pass data with end_date
export const endCycle = (data) => API.post("/cycle/end/", data);