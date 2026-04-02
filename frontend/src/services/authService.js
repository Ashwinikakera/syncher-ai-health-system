import API from "../api/axios";

export const registerUser = (data) => API.post("/register", data);
export const loginUser = (data) => API.post("/login", data);

// This file manages authentication by sending user registration and login data to backend APIs using axios instance, enabling secure user access and is used by Login.jsx and Register.jsx to handle auth flow and token-based communication