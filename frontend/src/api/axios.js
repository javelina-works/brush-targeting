import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000', // Default to FastAPI backend
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' }
});

export default api;
