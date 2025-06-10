import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { notificationServices } from '../api/services';
import { NotificationStatsResponse } from '../types/api';
import PushNotificationService from '../services/pushNotificationService';
import DeepLinkingService from '../services/deepLinkingService';
import * as Notifications from 'expo-notifications';

interface NotificationContextType {
  stats: NotificationStatsResponse | null;
  unreadCount: number;
  refreshStats: () => Promise<void>;
  loading: boolean;
  pushToken: string | null;
  initializePushNotifications: () => Promise<void>;
  scheduleMedicationReminder: (medicationName: string, dosage: string, time: Date) => Promise<string | null>;
  cancelMedicationReminder: (notificationId: string) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [stats, setStats] = useState<NotificationStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [pushToken, setPushToken] = useState<string | null>(null);

  const pushService = PushNotificationService.getInstance();
  const deepLinkService = DeepLinkingService.getInstance();

  const refreshStats = async () => {
    try {
      setLoading(true);
      const response = await notificationServices.getNotificationStats();
      setStats(response.data);
      
      // Update badge count
      await pushService.setBadgeCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch notification stats:', error);
      // Use dummy stats for fallback
      setStats({
        total_count: 5,
        unread_count: 3,
        by_severity: {
          critical: 1,
          high: 1,
          medium: 2,
          low: 1,
        },
        by_type: {
          interaction_alert: 2,
          risk_alert: 1,
          medication_reminder: 1,
          lab_followup: 1,
          symptom_monitoring: 0,
          general_info: 0,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const initializePushNotifications = async () => {
    try {
      // Register for push notifications
      const token = await pushService.registerForPushNotifications();
      setPushToken(token);

      // Set up notification listeners
      pushService.setupNotificationListeners(
        // When notification is received while app is in foreground
        (notification: Notifications.Notification) => {
          console.log('Foreground notification received:', notification);
          // Refresh stats to show new notification
          refreshStats();
        },
        // When user taps on notification
        (response: Notifications.NotificationResponse) => {
          console.log('Notification tapped:', response);
          const data = response.notification.request.content.data;
          
          if (data && typeof data === 'object') {
            // Handle deep linking
            deepLinkService.handleNotificationNavigation(data as any);
          }
          
          // Refresh stats
          refreshStats();
        }
      );

      console.log('Push notifications initialized successfully');
    } catch (error) {
      console.error('Failed to initialize push notifications:', error);
    }
  };

  const scheduleMedicationReminder = async (
    medicationName: string, 
    dosage: string, 
    time: Date
  ): Promise<string | null> => {
    try {
      const notificationId = await pushService.scheduleMedicationReminder(
        medicationName,
        dosage,
        time,
        true // repeat daily
      );
      
      if (notificationId) {
        console.log(`Scheduled medication reminder for ${medicationName}: ${notificationId}`);
      }
      
      return notificationId;
    } catch (error) {
      console.error('Failed to schedule medication reminder:', error);
      return null;
    }
  };

  const cancelMedicationReminder = async (notificationId: string): Promise<void> => {
    try {
      await pushService.cancelNotification(notificationId);
      console.log(`Cancelled medication reminder: ${notificationId}`);
    } catch (error) {
      console.error('Failed to cancel medication reminder:', error);
    }
  };

  useEffect(() => {
    refreshStats();
    
    // Initialize push notifications
    initializePushNotifications();
    
    // Poll for updates every 30 seconds
    const interval = setInterval(refreshStats, 30000);
    
    return () => {
      clearInterval(interval);
      // Clean up notification listeners
      pushService.removeNotificationListeners();
    };
  }, []);

  const unreadCount = stats?.unread_count || 0;

  const value: NotificationContextType = {
    stats,
    unreadCount,
    refreshStats,
    loading,
    pushToken,
    initializePushNotifications,
    scheduleMedicationReminder,
    cancelMedicationReminder,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

// Hook specifically for just getting the unread count (commonly used)
export const useUnreadNotificationCount = (): number => {
  const { unreadCount } = useNotifications();
  return unreadCount;
}; 