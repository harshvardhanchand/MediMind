import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';

interface AnalyticsEvent {
  event: string;
  properties?: Record<string, any>;
  timestamp: number;
  userId?: string;
  sessionId: string;
}

class SimpleAnalytics {
  private sessionId: string;
  private userId?: string;
  private events: AnalyticsEvent[] = [];

  constructor() {
    this.sessionId = this.generateSessionId();
    this.loadUserId();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async loadUserId() {
    try {
      this.userId = await AsyncStorage.getItem('analytics_user_id') || undefined;
    } catch (error) {
      console.error('Failed to load user ID:', error);
    }
  }

  async setUserId(userId: string) {
    this.userId = userId;
    try {
      await AsyncStorage.setItem('analytics_user_id', userId);
    } catch (error) {
      console.error('Failed to save user ID:', error);
    }
  }

  // Track basic events
  track(event: string, properties?: Record<string, any>) {
    const analyticsEvent: AnalyticsEvent = {
      event,
      properties: {
        ...properties,
        platform: DeviceInfo.getSystemName(),
        version: DeviceInfo.getVersion(),
      },
      timestamp: Date.now(),
      userId: this.userId,
      sessionId: this.sessionId,
    };

    this.events.push(analyticsEvent);
    this.saveEvent(analyticsEvent);
    
    // Log for debugging (remove in production)
    console.log('Analytics Event:', analyticsEvent);
  }

  private async saveEvent(event: AnalyticsEvent) {
    try {
      const existingEvents = await AsyncStorage.getItem('analytics_events');
      const events = existingEvents ? JSON.parse(existingEvents) : [];
      events.push(event);
      
      // Keep only last 1000 events to prevent storage bloat
      if (events.length > 1000) {
        events.splice(0, events.length - 1000);
      }
      
      await AsyncStorage.setItem('analytics_events', JSON.stringify(events));
    } catch (error) {
      console.error('Failed to save analytics event:', error);
    }
  }

  // Track app lifecycle
  async trackAppOpen() {
    const lastOpen = await AsyncStorage.getItem('last_app_open');
    const now = Date.now();
    
    if (lastOpen) {
      const daysSinceLastOpen = (now - parseInt(lastOpen)) / (1000 * 60 * 60 * 24);
      this.track('app_opened', { 
        days_since_last_open: Math.floor(daysSinceLastOpen),
        returning_user: true 
      });
    } else {
      this.track('app_opened', { 
        first_time: true,
        returning_user: false 
      });
    }
    
    await AsyncStorage.setItem('last_app_open', now.toString());
  }

  // Track screen views
  trackScreenView(screenName: string) {
    this.track('screen_view', { screen_name: screenName });
  }

  // Track feature usage
  trackFeatureUsage(feature: string, action: string, properties?: Record<string, any>) {
    this.track('feature_usage', { 
      feature, 
      action, 
      ...properties 
    });
  }

  // Track user actions
  trackUserAction(action: string, properties?: Record<string, any>) {
    this.track('user_action', { 
      action, 
      ...properties 
    });
  }

  // Get basic retention data
  async getRetentionData() {
    try {
      const events = await AsyncStorage.getItem('analytics_events');
      if (!events) return null;

      const parsedEvents = JSON.parse(events);
      const appOpenEvents = parsedEvents.filter((e: AnalyticsEvent) => e.event === 'app_opened');
      
      return {
        total_sessions: appOpenEvents.length,
        first_open: appOpenEvents[0]?.timestamp,
        last_open: appOpenEvents[appOpenEvents.length - 1]?.timestamp,
        unique_days: new Set(appOpenEvents.map((e: AnalyticsEvent) => 
          new Date(e.timestamp).toDateString()
        )).size
      };
    } catch (error) {
      console.error('Failed to get retention data:', error);
      return null;
    }
  }

  // Export data for analysis (useful for early stage)
  async exportData() {
    try {
      const events = await AsyncStorage.getItem('analytics_events');
      return events ? JSON.parse(events) : [];
    } catch (error) {
      console.error('Failed to export analytics data:', error);
      return [];
    }
  }
}

export const analytics = new SimpleAnalytics(); 