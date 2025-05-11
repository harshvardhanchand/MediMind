import 'react-native-url-polyfill/auto'; // Required for Supabase to work in React Native
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

// Expo Go doesn't support AsyncStorage directly, SecureStore is recommended for tokens.
// Supabase uses localStorage by default, this adapter makes it use SecureStore.
const ExpoSecureStoreAdapter = {
  getItem: (key: string) => {
    return SecureStore.getItemAsync(key);
  },
  setItem: (key: string, value: string) => {
    SecureStore.setItemAsync(key, value);
  },
  removeItem: (key: string) => {
    SecureStore.deleteItemAsync(key);
  },
};

const supabaseUrl = Constants.expoConfig?.extra?.supabaseUrl as string | undefined;
const supabaseAnonKey = Constants.expoConfig?.extra?.supabaseAnonKey as string | undefined;

if (!supabaseUrl || !supabaseAnonKey) {
  const message = "Supabase URL or Anon Key is missing. Check app.json (extra field) or app.config.js.";
  console.error(message);
  // In a real app, you might throw an error or display a message to the user
  // For now, we'll proceed, but Supabase client will be null.
}

// Initialize Supabase client only if URL and Key are present
export const supabase: SupabaseClient | null = 
  (supabaseUrl && supabaseAnonKey) 
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        storage: ExpoSecureStoreAdapter as any, // Use SecureStore for session persistence
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false, // Necessary for React Native
      },
    })
  : null;

if (!supabase) {
    console.warn("Supabase client could not be initialized. Authentication and Supabase-related features will not work.")
} 