import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Error messages that should be silently handled (no toast)
const SILENT_ERRORS = [
  'already exists',
];

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    const messageLower = message.toLowerCase();
    
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('auth_token');
      if (typeof window !== 'undefined') {
        window.location.hash = '#/login';
      }
    } else if (!SILENT_ERRORS.some(err => messageLower.includes(err))) {
      // Only show toast if not a silent error
      toast.error(message);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
