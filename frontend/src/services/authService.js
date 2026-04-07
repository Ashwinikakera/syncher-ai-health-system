import API from "../api/axios";

export const registerUser = (data) => API.post("/register", data);  // ← added /

export const loginUser = async (data) => {
  const response = await API.post("/login", data);  // ← added /
  localStorage.setItem("token", response.data.token);
  return response;
};