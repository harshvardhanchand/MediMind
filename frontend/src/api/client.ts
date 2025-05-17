import axios from 'axios';
import { API_URL } from '../config';
import * as SecureStore from 'expo-secure-store';

const AUTH_TOKEN_KEY = 'auth_token'; // Ensure this matches the key used in AuthContext

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Mark to prevent infinite retry loops
      
      console.error(
        'API Error: 401 Unauthorized. Attempting to clear stored auth token.'
      );
      try {
        await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
        console.log('Auth token cleared from SecureStore due to 401.');
        // Ideally, we would trigger a global sign-out state update here.
        // For now, removing the token means the next auth check (e.g., app restart, 
        // or a mechanism in AuthContext that re-validates on API failure) should 
        // redirect to login. A more immediate redirect could be forced via a global event emitter
        // or by having a callback to a navigation/auth service if a less direct coupling is desired.
      } catch (e) {
        console.error('Failed to clear auth token from SecureStore after 401:', e);
      }
      // It's important to still reject the promise so the original caller can handle the error.
      // The UI should ideally react to this by, for instance, navigating to login if a user-specific action failed.
    }
    
    return Promise.reject(error);
  }
);

export default apiClient; 