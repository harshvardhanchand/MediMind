import axios from 'axios';
import { API_URL } from '../config';
import { supabaseClient } from '../services/supabase';

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
    // Get token from Supabase session instead of manual storage
    const { data: { session } } = await supabaseClient.auth.getSession();
    const token = session?.access_token;
    
    console.log('🔍 API Request Debug:', {
      url: config.url,
      method: config.method,
      hasToken: !!token,
      tokenPrefix: token ? token.substring(0, 20) + '...' : 'none',
      tokenLength: token ? token.length : 0,
      tokenParts: token ? token.split('.').length : 0,
      sessionExists: !!session,
      sessionUser: session?.user?.id || 'none'
    });
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.warn('⚠️ No token found in Supabase session');
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
      // Let Supabase handle token refresh automatically
      // If refresh fails, the AuthContext will detect it and show login screen
    }
    
    return Promise.reject(error);
  }
);

export default apiClient; 