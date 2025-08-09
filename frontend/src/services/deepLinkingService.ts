import { NavigationContainerRef } from '@react-navigation/native';
import { PushNotificationData } from './pushNotificationService';

export interface DeepLinkData {
  screen: string;
  params?: Record<string, any>;
}

class DeepLinkingService {
  private static instance: DeepLinkingService;
  private navigationRef: NavigationContainerRef<any> | null = null;

  static getInstance(): DeepLinkingService {
    if (!DeepLinkingService.instance) {
      DeepLinkingService.instance = new DeepLinkingService();
    }
    return DeepLinkingService.instance;
  }

  setNavigationRef(ref: NavigationContainerRef<any>) {
    this.navigationRef = ref;
  }

  handleNotificationNavigation(notificationData: PushNotificationData) {
    if (!this.navigationRef?.isReady()) {
      console.warn('Navigation not ready, queuing notification navigation');
      // Could implement a queue here if needed
      return;
    }

    const linkData = this.parseNotificationData(notificationData);
    if (linkData) {
      this.navigateToScreen(linkData.screen, linkData.params);
    }
  }

  private parseNotificationData(data: PushNotificationData): DeepLinkData | null {
    switch (data.type) {
      case 'interaction_alert':
      case 'risk_alert':
        // Navigate to notifications screen and highlight specific notification
        return {
          screen: 'NotificationScreen',
          params: { 
            highlightNotification: data.notificationId,
            filterType: data.type 
          }
        };

      case 'medication_reminder':
        // Navigate to specific medication or medication list
        if (data.entityId) {
          return {
            screen: 'MedicationDetail',
            params: { medicationId: data.entityId }
          };
        }
        return {
          screen: 'MedicationsScreen',
          params: {}
        };

      case 'lab_followup':
        // Navigate to health data tab; pass lab result id if available
        if (data.entityId) {
          return {
            screen: 'DataTab',
            params: { labResultId: data.entityId }
          };
        }
        return {
          screen: 'DataTab',
          params: {}
        };

      case 'symptom_monitoring':
        // Navigate to symptom tracker
        return {
          screen: 'SymptomTracker',
          params: {}
        };

      case 'general_info':
      default:
        // Navigate to notifications screen
        return {
          screen: 'NotificationScreen',
          params: { highlightNotification: data.notificationId }
        };
    }
  }

  private navigateToScreen(screenName: string, params?: Record<string, any>) {
    try {
      console.log(`Navigating to ${screenName} with params:`, params);

      const tabScreens = ['DashboardTab', 'DocumentsTab', 'DataTab', 'AssistantTab', 'SettingsTab'];
      const dashboardStackScreens = new Set([
        'Home', 'Upload', 'Vitals', 'SymptomTracker', 'MedicationsScreen', 'AddMedication',
        'MedicationDetail', 'AddSymptom', 'HealthReadings', 'AddHealthReading', 'Query',
        'DocumentDetail', 'DataReview', 'NotificationScreen', 'EditProfile'
      ]);

      if (tabScreens.includes(screenName)) {
        // Navigate to a tab inside Main
        this.navigationRef?.navigate('Main', { screen: screenName, params });
        return;
      }

      if (dashboardStackScreens.has(screenName)) {
        // Navigate to a screen inside Dashboard stack
        this.navigationRef?.navigate('Main', {
          screen: 'DashboardTab',
          params: { screen: screenName, params }
        });
        return;
      }

      // Fallback: try direct navigation
      this.navigationRef?.navigate(screenName as any, params as any);
    } catch (error) {
      console.error('Error navigating to screen:', error);
      // Fallback to main dashboard
      this.navigationRef?.navigate('Main', { screen: 'DashboardTab' });
    }
  }

  private isTabScreen(screenName: string): boolean {
    const tabScreens = [
      'DashboardTab',
      'DocumentsTab', 
      'DataTab',
      'AssistantTab',
      'SettingsTab'
    ];
    return tabScreens.includes(screenName);
  }

  // Handle custom URL schemes if needed
  handleDeepLink(url: string) {
    try {
      const urlObject = new URL(url);
      const screen = urlObject.pathname.replace('/', '');
      const params = Object.fromEntries(urlObject.searchParams.entries());
      
      this.navigateToScreen(screen, params);
    } catch (error) {
      console.error('Error parsing deep link:', error);
    }
  }

  // Generate deep link URLs for sharing
  generateNotificationDeepLink(notificationData: PushNotificationData): string {
    const baseUrl = 'https://www.medimind.co.in/';
    const linkData = this.parseNotificationData(notificationData);
    
    if (!linkData) return baseUrl;
    
    const url = new URL(linkData.screen, baseUrl);
    if (linkData.params) {
      Object.entries(linkData.params).forEach(([key, value]) => {
        url.searchParams.set(key, String(value));
      });
    }
    
    return url.toString();
  }
}

export default DeepLinkingService; 