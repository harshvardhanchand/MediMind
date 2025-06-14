import axios from 'axios';

import { API_URL } from '../config';
import { supabaseClient } from '../services/supabase';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Cache the current session to avoid repeated getSession() calls
let cachedSession: any = null;
let sessionCacheTime = 0;
const SESSION_CACHE_DURATION = 5000; // 5 seconds

// Add request interceptor to attach auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      // Use cached session if it's recent
      const now = Date.now();
      if (cachedSession && (now - sessionCacheTime) < SESSION_CACHE_DURATION) {
        const token = cachedSession?.access_token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      }

      // Get fresh session if cache is stale
      const { data } = await supabaseClient.auth.getSession();
      cachedSession = data.session;
      sessionCacheTime = now;
      
      const token = data.session?.access_token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      } else {
        console.warn('⚠️ No token found in Supabase session');
      }
    } catch (error) {
      console.error('Error getting session for API request:', error);
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
      originalRequest._retry = true;
      
      console.error('API Error: 401 Unauthorized. Session might be expired.');
      // Clear cached session on 401
      cachedSession = null;
      sessionCacheTime = 0;
      
      // Let Supabase handle token refresh automatically
      // If refresh fails, the AuthContext will detect it and show login screen
    }
    
    return Promise.reject(error);
  }
);

export default apiClient; 