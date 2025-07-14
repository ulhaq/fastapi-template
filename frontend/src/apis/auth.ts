import axios from "@/apis/base";

export default {
  async getToken(email: string, password: string) {
    const response = await axios.post(
      "/auth/token",
      { username: email, password: password },
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );
    return response.data;
  },

  async refreshToken() {
    const response = await axios.post("/auth/refresh");
    return response.data;
  },

  async logout() {
    const response = await axios.post("/auth/logout");
    return response.data;
  },

  async getAuthenticatedUser() {
    const response = await axios.get("/users/me");
    return response.data;
  },
};
