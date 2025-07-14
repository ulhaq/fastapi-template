import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "@/stores/auth";

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

let requestQueue: Array<(token: string) => void> = [];

const queueFailedRequest = (callback: (token: string) => void) => {
  requestQueue.push(callback);
};

const resolveFailedRequests = (token: string) => {
  requestQueue.forEach((cb) => cb(token));
  requestQueue = [];
};

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const authStore = useAuthStore();

  if (authStore.accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const authStore = useAuthStore();
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (authStore.loading) {
      await authStore.logout();
      return Promise.reject(error);
    }

    if (authStore.loading) {
      return new Promise((resolve) => {
        queueFailedRequest((newToken: string) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          resolve(apiClient(originalRequest));
        });
      });
    }

    try {
      authStore.loading = true;

      const newToken = await authStore.refreshToken();

      resolveFailedRequests(newToken);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
      }

      return apiClient(originalRequest);
    } catch (refreshError) {
      await authStore.logout();
      return Promise.reject(
        refreshError instanceof Error
          ? refreshError
          : new Error(String(refreshError))
      );
    } finally {
      authStore.loading = false;
    }
  }
);

export default apiClient;
