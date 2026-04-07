import API from "../api/axios";

export const askChatbot = (question) =>
  API.post("chat/", { question });
