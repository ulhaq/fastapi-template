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

  async register(name: string, email: string, password: string) {
    const response = await axios.post("/auth/register", {
      name: name,
      email: email,
      password: password,
    });
    return response.data;
  },

  async requestPasswordReset(email: string) {
    await axios.post("/auth/reset-password", {
      email: email,
    });
  },

  async resetPassword(password: string, token: string) {
    let response = await axios.post(`/auth/reset-password/${token}`, {
      password: password,
    });
    return response.data;
  },
};
