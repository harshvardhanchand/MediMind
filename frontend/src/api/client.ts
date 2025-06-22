import axios from 'axios';
import Constants from 'expo-constants';
import { API_URL } from '../config';
import { supabaseClient } from '../services/supabase';

// Generate a simple UUID for correlation IDs
const generateCorrelationId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};


const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});


let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};


apiClient.interceptors.request.use(
  async (config) => {
    try {
      // Add correlation ID and app version for better debugging
      config.headers['X-Request-ID'] = generateCorrelationId();
      config.headers['X-App-Version'] = Constants.expoConfig?.version || 'unknown';
      config.headers['X-Platform'] = 'mobile';
      
      // Let Supabase handle token refresh automatically
      const { data } = await supabaseClient.auth.getSession();
      
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


apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      console.warn('🔄 401 Unauthorized - Attempting token refresh and retry...');
      
      if (isRefreshing) {
        
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }
      
      isRefreshing = true;
      
      try {
        
        const { data: refreshed, error: refreshError } = await supabaseClient.auth.getSession();
        
        if (refreshError || !refreshed.session?.access_token) {
          console.error('❌ Token refresh failed:', refreshError);
          processQueue(refreshError || new Error('No session after refresh'), null);
          
         
          return Promise.reject(error);
        }
        
        const newToken = refreshed.session.access_token;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        
        processQueue(null, newToken);
        
        console.log('✅ Token refreshed successfully, retrying original request');
        return apiClient(originalRequest);
        
      } catch (refreshError) {
        console.error('❌ Token refresh failed with exception:', refreshError);
        processQueue(refreshError, null);
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient; 