import API from "../api/axios";

export const addCycle  = (data) => API.post("/cycle/", data);
export const getCycles = ()     => API.get("/cycle/");