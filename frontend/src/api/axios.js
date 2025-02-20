import axios from 'axios';

/**
 * Collect from VITE_API_URL env OR
 * if we are in dev, get localhost:8000, else just local server.
 */
const apiBaseURL = import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : "/");

const api = axios.create({
  baseURL: apiBaseURL,
  // timeout: 5000,
  headers: { 'Content-Type': 'application/json' }
});

export default api;
