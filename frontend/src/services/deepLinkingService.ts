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
          screen: 'NotificationsTab',
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
        // Navigate to specific lab result or health data screen
        if (data.entityId) {
          return {
            screen: 'LabResultDetail',
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
          screen: 'NotificationsTab',
          params: { highlightNotification: data.notificationId }
        };
    }
  }

  private navigateToScreen(screenName: string, params?: Record<string, any>) {
    try {
      console.log(`Navigating to ${screenName} with params:`, params);
      
      // Handle tab navigation vs stack navigation
      if (this.isTabScreen(screenName)) {
        this.navigationRef?.navigate(screenName, params);
      } else {
        // For stack screens, we might need to navigate to a tab first
        this.navigationRef?.navigate(screenName, params);
      }
    } catch (error) {
      console.error('Error navigating to screen:', error);
      // Fallback to notifications tab
      this.navigationRef?.navigate('NotificationsTab');
    }
  }

  private isTabScreen(screenName: string): boolean {
    const tabScreens = [
      'DashboardTab',
      'DocumentsTab', 
      'DataTab',
      'NotificationsTab',
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
    const baseUrl = 'medimind://';
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