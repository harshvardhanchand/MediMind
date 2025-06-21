import PushNotification from 'react-native-push-notification';
import DeviceInfo from 'react-native-device-info';
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

class PushNotificationService {
  private static instance: PushNotificationService;
  private pushToken: string | null = null;
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
      if (Platform.OS === 'ios') {
        const permissions = await PushNotification.requestPermissions();
        return !!(permissions.alert && permissions.sound);
      }
      
      // Android permissions are handled automatically
      return true;
    } catch (error) {
      console.error('Failed to request permissions:', error);
      return false;
    }
  }

  async registerForPushNotifications(): Promise<string | null> {
    try {
      if (this.isInitialized) {
        return this.pushToken;
      }

      // Configure push notifications
      PushNotification.configure({
        // Called when Token is generated (iOS and Android)
        onRegister: (token) => {
          console.log('Push Token:', token);
          this.pushToken = token.token;
        },

        // Called when a remote notification is received while app is in foreground
        onNotification: (notification) => {
          console.log('Notification received:', notification);
          
          // Handle notification tap
          if (notification.userInteraction && this.responseListener) {
            this.responseListener({
              notification: {
                request: {
                  content: {
                    data: notification.userInfo || notification.data || {}
                  }
                }
              }
            });
          } else if (this.notificationListener) {
            this.notificationListener(notification);
          }
          
          // Required on iOS only
          notification.finish && notification.finish();
        },

        // Should the initial notification be popped automatically
        popInitialNotification: true,

        // iOS only properties
        permissions: {
          alert: true,
          badge: true,
          sound: true,
        },

        // Android only properties
        requestPermissions: Platform.OS === 'ios',
      });

      // Create notification channels for Android
      if (Platform.OS === 'android') {
        PushNotification.createChannel(
          {
            channelId: 'medical-alerts',
            channelName: 'Medical Alerts',
            channelDescription: 'Critical medical alerts and notifications',
            playSound: true,
            soundName: 'default',
            importance: 4, // HIGH
            vibrate: true,
          },
          (created) => console.log(`Medical alerts channel created: ${created}`)
        );

        PushNotification.createChannel(
          {
            channelId: 'medication-reminders',
            channelName: 'Medication Reminders',
            channelDescription: 'Daily medication reminder notifications',
            playSound: true,
            soundName: 'default',
            importance: 3, // DEFAULT
            vibrate: true,
          },
          (created) => console.log(`Medication reminders channel created: ${created}`)
        );
      }

      const hasPermissions = await this.requestPermissions();
      if (!hasPermissions) {
        console.log('Push notification permissions denied');
        return null;
      }

      // For testing, we'll use device ID as token since we're not using a push service
      const deviceId = await DeviceInfo.getUniqueId();
      this.pushToken = `native_${deviceId}`;
      this.isInitialized = true;
      
      console.log('Native push notifications registered:', this.pushToken);
      return this.pushToken;
    } catch (error) {
      console.error('Error registering for push notifications:', error);
      return null;
    }
  }

  setupNotificationListeners(
    onNotificationReceived?: (notification: any) => void,
    onNotificationResponse?: (response: any) => void
  ) {
    this.notificationListener = onNotificationReceived;
    this.responseListener = onNotificationResponse;
    console.log('Native notification listeners configured');
  }

  removeNotificationListeners() {
    this.notificationListener = null;
    this.responseListener = null;
    console.log('Native notification listeners removed');
  }

  async scheduleMedicationReminder(
    medicationName: string,
    dosage: string,
    time: Date,
    repeatDaily: boolean = true
  ): Promise<string | null> {
    try {
      const notificationId = Math.floor(Math.random() * 1000000).toString();
      
      const scheduleDate = new Date(time);
      
      if (repeatDaily) {
        // Schedule repeating notification
        PushNotification.localNotificationSchedule({
          id: notificationId,
          title: 'Medication Reminder',
          message: `Time to take your ${medicationName} (${dosage})`,
          date: scheduleDate,
          repeatType: 'day',
          channelId: 'medication-reminders',
          userInfo: {
            type: 'medication_reminder',
            medicationName,
            dosage,
            notificationId,
          },
          actions: ['Take', 'Snooze'],
          playSound: true,
          soundName: 'default',
        });
      } else {
        // Schedule one-time notification
        PushNotification.localNotificationSchedule({
          id: notificationId,
          title: 'Medication Reminder',
          message: `Time to take your ${medicationName} (${dosage})`,
          date: scheduleDate,
          channelId: 'medication-reminders',
          userInfo: {
            type: 'medication_reminder',
            medicationName,
            dosage,
            notificationId,
          },
          playSound: true,
          soundName: 'default',
        });
      }

      console.log(`Scheduled medication reminder: ${notificationId} for ${scheduleDate}`);
      return notificationId;
    } catch (error) {
      console.error('Error scheduling medication reminder:', error);
      return null;
    }
  }

  async cancelNotification(notificationId: string): Promise<void> {
    try {
      PushNotification.cancelLocalNotifications({
        id: notificationId,
      });
      console.log(`Cancelled notification: ${notificationId}`);
    } catch (error) {
      console.error('Error cancelling notification:', error);
    }
  }

  async cancelAllNotifications(): Promise<void> {
    try {
      PushNotification.cancelAllLocalNotifications();
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
      const notificationId = Math.floor(Math.random() * 1000000).toString();
      
      PushNotification.localNotification({
        id: notificationId,
        title,
        message: body,
        channelId: this.getNotificationChannel(data?.type || 'general_info'),
        userInfo: data || {},
        playSound: true,
        soundName: 'default',
      });

      console.log(`Sent local notification: ${notificationId}`);
      return notificationId;
    } catch (error) {
      console.error('Error sending local notification:', error);
      return null;
    }
  }

  async getBadgeCount(): Promise<number> {
    return new Promise((resolve) => {
      PushNotification.getApplicationIconBadgeNumber((number) => {
        resolve(number);
      });
    });
  }

  async setBadgeCount(count: number): Promise<void> {
    try {
      PushNotification.setApplicationIconBadgeNumber(count);
      console.log(`Set badge count to: ${count}`);
    } catch (error) {
      console.error('Error setting badge count:', error);
    }
  }

  getExpoPushToken(): string | null {
    return this.pushToken;
  }

  getNotificationChannel(type: PushNotificationData['type']): string {
    switch (type) {
      case 'interaction_alert':
      case 'risk_alert':
        return 'medical-alerts';
      case 'medication_reminder':
        return 'medication-reminders';
      default:
        return Platform.OS === 'android' ? 'medical-alerts' : 'default';
    }
  }
}

export default PushNotificationService; 