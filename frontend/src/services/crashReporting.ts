import * as Sentry from '@sentry/react-native';
import Constants from 'expo-constants';
import { analytics } from './analytics';

// Sentry configuration
const SENTRY_DSN = Constants.expoConfig?.extra?.sentryDsn || 'YOUR_SENTRY_DSN_HERE';

class CrashReportingService {
  private initialized = false;

  init() {
    if (this.initialized) return;

    try {
      Sentry.init({
        dsn: SENTRY_DSN,
        debug: __DEV__,
        environment: __DEV__ ? 'development' : 'production',
        enableAutoSessionTracking: true,
        sessionTrackingIntervalMillis: 30000,
        // Adds more context data to events (IP address, cookies, user, etc.)
        sendDefaultPii: true,
        beforeSend: (event) => {
          // Filter out development errors in production
          if (!__DEV__ && event.environment === 'development') {
            return null;
          }
          return event;
        },
        tracesSampleRate: __DEV__ ? 1.0 : 0.1, // 100% in dev, 10% in prod
      });

      this.initialized = true;
      console.log('✅ Crash reporting initialized with DSN:', SENTRY_DSN.substring(0, 50) + '...');
    } catch (error) {
      console.error('❌ Failed to initialize crash reporting:', error);
    }
  }

  // Set user context for crash reports
  setUser(userId: string, email?: string) {
    if (!this.initialized) return;

    Sentry.setUser({
      id: userId,
      email: email,
    });
  }

  // Clear user context (on logout)
  clearUser() {
    if (!this.initialized) return;

    Sentry.setUser(null);
  }

  // Set additional context
  setContext(key: string, context: any) {
    if (!this.initialized) return;

    Sentry.setContext(key, context);
  }

  // Add breadcrumb for debugging
  addBreadcrumb(message: string, category: string = 'user-action', level: 'info' | 'warning' | 'error' = 'info') {
    if (!this.initialized) return;

    Sentry.addBreadcrumb({
      message,
      category,
      level,
      timestamp: Date.now() / 1000,
    });
  }

  // Capture exception manually
  captureException(error: Error, context?: any) {
    if (!this.initialized) {
      console.error('Crash reporting not initialized, logging error:', error);
      return;
    }

    // Also track in local analytics
    analytics.track('error_captured', {
      error_message: error.message,
      error_stack: error.stack,
      context: context,
    });

    Sentry.withScope((scope) => {
      if (context) {
        scope.setContext('additional_context', context);
      }
      Sentry.captureException(error);
    });
  }

  // Capture message (for non-error events)
  captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info', context?: any) {
    if (!this.initialized) {
      console.log('Crash reporting not initialized, logging message:', message);
      return;
    }

    Sentry.withScope((scope) => {
      if (context) {
        scope.setContext('message_context', context);
      }
      Sentry.captureMessage(message, level);
    });
  }

  // Test crash reporting (development only)
  testCrash() {
    if (!__DEV__) return;
    
    console.log('🧪 Testing crash reporting...');
    this.captureException(new Error('Test crash from MediMind app'));
  }
}

export const crashReporting = new CrashReportingService(); 