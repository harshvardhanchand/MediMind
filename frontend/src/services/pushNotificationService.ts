import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

export interface PushNotificationData extends Record<string, unknown> {
  type: 'interaction_alert' | 'risk_alert' | 'medication_reminder' | 'lab_followup' | 'symptom_monitoring' | 'general_info';
  notificationId?: string;
  entityType?: string;
  entityId?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  body: string;
}

// Configure how notifications are handled when received
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

class PushNotificationService {
  private static instance: PushNotificationService;
  private expoPushToken: string | null = null;
  private isInitialized: boolean = false;
  private notificationListener: any = null;
  private responseListener: any = null;

  static getInstance(): PushNotificationService {
    if (!PushNotificationService.instance) {
      PushNotificationService.instance = new PushNotificationService();
    }
    return PushNotificationService.instance;
  }

  async requestPermissions(): Promise<boolean> {
    try {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      
      return finalStatus === 'granted';
    } catch (error) {
      console.error('Failed to request permissions:', error);
      return false;
    }
  }

  async registerForPushNotifications(): Promise<string | null> {
    try {
      if (this.isInitialized && this.expoPushToken) {
        return this.expoPushToken;
      }

      // Check if device can receive push notifications
      if (!Device.isDevice) {
        console.log('Must use physical device for Push Notifications');
        return null;
      }

      // Request permissions
      const hasPermissions = await this.requestPermissions();
      if (!hasPermissions) {
        console.log('Push notification permissions denied');
        return null;
      }

      // Configure notification channels for Android
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('medical-alerts', {
          name: 'Medical Alerts',
          description: 'Critical medical alerts and notifications',
          importance: Notifications.AndroidImportance.HIGH,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#FF231F7C',
          sound: 'default',
        });

        await Notifications.setNotificationChannelAsync('medication-reminders', {
          name: 'Medication Reminders',
          description: 'Daily medication reminder notifications',
          importance: Notifications.AndroidImportance.DEFAULT,
          vibrationPattern: [0, 250, 250, 250],
          sound: 'default',
        });
      }

      // Get Expo push token
      const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
      if (!projectId) {
        console.warn('No project ID found for push notifications');
        // For development, create a mock token
        this.expoPushToken = `expo_dev_${Device.osBuildId || 'unknown'}`;
      } else {
        const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
        this.expoPushToken = tokenData.data;
      }

      this.isInitialized = true;
      console.log('Expo push notifications registered:', this.expoPushToken);
      return this.expoPushToken;
    } catch (error) {
      console.error('Error registering for push notifications:', error);
      return null;
    }
  }

  setupNotificationListeners(
    onNotificationReceived?: (notification: any) => void,
    onNotificationResponse?: (response: any) => void
  ) {
    // Remove existing listeners
    this.removeNotificationListeners();

    // Set up notification received listener (when app is in foreground)
    if (onNotificationReceived) {
      this.notificationListener = Notifications.addNotificationReceivedListener(onNotificationReceived);
    }

    // Set up notification response listener (when user taps notification)
    if (onNotificationResponse) {
      this.responseListener = Notifications.addNotificationResponseReceivedListener(onNotificationResponse);
    }

    console.log('Expo notification listeners configured');
  }

  removeNotificationListeners() {
    if (this.notificationListener) {
      this.notificationListener.remove();
      this.notificationListener = null;
    }
    if (this.responseListener) {
      this.responseListener.remove();
      this.responseListener = null;
    }
    console.log('Expo notification listeners removed');
  }

  async scheduleMedicationReminder(
    medicationName: string,
    dosage: string,
    time: Date,
    repeatDaily: boolean = true
  ): Promise<string | null> {
    try {
      const notificationId = Math.floor(Math.random() * 1000000).toString();
      
      const trigger = repeatDaily 
        ? {
            hour: time.getHours(),
            minute: time.getMinutes(),
            repeats: true,
          } as Notifications.NotificationTriggerInput
        : { date: time } as Notifications.NotificationTriggerInput;

      await Notifications.scheduleNotificationAsync({
        identifier: notificationId,
        content: {
          title: 'Medication Reminder',
          body: `Time to take your ${medicationName} (${dosage})`,
          data: {
            type: 'medication_reminder',
            medicationName,
            dosage,
            notificationId,
          },
          sound: 'default',
          categoryIdentifier: 'medication',
        },
        trigger,
      });

      console.log(`Scheduled medication reminder: ${notificationId}`);
      return notificationId;
    } catch (error) {
      console.error('Error scheduling medication reminder:', error);
      return null;
    }
  }

  async scheduleFollowUpReminder(
    title: string,
    message: string,
    triggerDate: Date,
    data?: PushNotificationData
  ): Promise<string | null> {
    try {
      const notificationId = Math.floor(Math.random() * 1000000).toString();
      
      await Notifications.scheduleNotificationAsync({
        identifier: notificationId,
        content: {
          title,
          body: message,
          data: {
            ...data,
            notificationId,
          },
          sound: 'default',
        },
                 trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: triggerDate },
      });

      console.log(`Scheduled follow-up reminder: ${notificationId}`);
      return notificationId;
    } catch (error) {
      console.error('Error scheduling follow-up reminder:', error);
      return null;
    }
  }

  async cancelNotification(notificationId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
      console.log(`Cancelled notification: ${notificationId}`);
    } catch (error) {
      console.error('Error cancelling notification:', error);
    }
  }

  async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
      console.log('Cancelled all scheduled notifications');
    } catch (error) {
      console.error('Error cancelling all notifications:', error);
    }
  }

  async sendLocalNotification(
    title: string,
    body: string,
    data?: PushNotificationData
  ): Promise<string | null> {
    try {
      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data: data || {},
          sound: 'default',
        },
        trigger: null, // Send immediately
      });

      console.log(`Sent local notification: ${notificationId}`);
      return notificationId;
    } catch (error) {
      console.error('Error sending local notification:', error);
      return null;
    }
  }

  async getBadgeCount(): Promise<number> {
    try {
      return await Notifications.getBadgeCountAsync();
    } catch (error) {
      console.error('Error getting badge count:', error);
      return 0;
    }
  }

  async setBadgeCount(count: number): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(count);
    } catch (error) {
      console.error('Error setting badge count:', error);
    }
  }

  getExpoPushToken(): string | null {
    return this.expoPushToken;
  }

  getNotificationChannel(type: PushNotificationData['type']): string {
    switch (type) {
      case 'interaction_alert':
      case 'risk_alert':
        return 'medical-alerts';
      case 'medication_reminder':
        return 'medication-reminders';
      case 'lab_followup':
      case 'symptom_monitoring':
      case 'general_info':
      default:
        return 'medical-alerts';
    }
  }
}

export default PushNotificationService.getInstance(); 