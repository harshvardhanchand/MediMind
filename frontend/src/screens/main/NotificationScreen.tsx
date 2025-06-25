import React, { useState, useCallback, useMemo } from 'react';
import { View, FlatList, RefreshControl, TouchableOpacity, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { styled } from 'nativewind';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import NotificationCard from '../../components/common/NotificationCard';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import { notificationServices } from '../../api/services';
import {
  NotificationResponse,
  NotificationStatsResponse,
  NotificationType,
  NotificationSeverity
} from '../../types/api';
import { crashReporting } from '../../services/crashReporting';
import { FilterOption } from '../../types/interfaces';

const StyledView = styled(View);

const NotificationScreen = () => {
  const { colors } = useTheme();
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [stats, setStats] = useState<NotificationStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [criticalError, setCriticalError] = useState<string | null>(null);

  // ✅ Memoized filter options - only created once
  const typeFilters = useMemo<FilterOption[]>(() => [
    { label: 'All', value: null },
    { label: 'Interactions', value: NotificationType.INTERACTION_ALERT },
    { label: 'Risk Alerts', value: NotificationType.RISK_ALERT },
    { label: 'Reminders', value: NotificationType.MEDICATION_REMINDER },
    { label: 'Lab Follow-up', value: NotificationType.LAB_FOLLOWUP },
    { label: 'Symptoms', value: NotificationType.SYMPTOM_MONITORING },
    { label: 'General', value: NotificationType.GENERAL_INFO },
  ], []);

  const severityFilters = useMemo<FilterOption[]>(() => [
    { label: 'All', value: null },
    { label: 'Critical', value: NotificationSeverity.CRITICAL },
    { label: 'High', value: NotificationSeverity.HIGH },
    { label: 'Medium', value: NotificationSeverity.MEDIUM },
    { label: 'Low', value: NotificationSeverity.LOW },
  ], []);

  useFocusEffect(
    useCallback(() => {
      fetchNotifications();
      fetchStats();
    }, [selectedFilter, selectedSeverity])
  );

  const fetchNotifications = async () => {
    try {
      setError(null);
      crashReporting.addBreadcrumb('Fetching notifications', 'api-request', 'info');

      const params: any = { limit: 50 };
      if (selectedFilter) params.notification_type = selectedFilter;
      if (selectedSeverity) params.severity = selectedSeverity;

      const response = await notificationServices.getNotifications(params);

      // If API returns empty array, use dummy data for demo
      if (response.data && response.data.length > 0) {
        setNotifications(response.data);
        crashReporting.addBreadcrumb('Notifications loaded successfully', 'api-response', 'info');
      } else {
        console.log('API returned empty notifications, using dummy data for demo');
        setNotifications(generateDummyNotifications());
      }
    } catch (apiError: any) {
      console.error('Failed to fetch notifications:', apiError);

      const errorMessage = apiError.response?.data?.detail || 'Failed to load notifications. Please try again.';
      setError(errorMessage);

      crashReporting.captureException(apiError, {
        context: 'notification_fetch',
        errorType: 'notification_api_error',
        statusCode: apiError.response?.status,
        filters: { selectedFilter, selectedSeverity },
      });

      // Use dummy data for demo
      setNotifications(generateDummyNotifications());
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await notificationServices.getNotificationStats();
      setStats(response.data);
    } catch (statsError: any) {
      console.error('Failed to fetch notification stats:', statsError);

      crashReporting.captureException(statsError, {
        context: 'notification_stats_fetch',
        errorType: 'notification_stats_error',
        statusCode: statsError.response?.status,
      });

      // Use dummy stats
      setStats({
        total_count: 12,
        unread_count: 5,
        by_severity: {
          [NotificationSeverity.CRITICAL]: 1,
          [NotificationSeverity.HIGH]: 2,
          [NotificationSeverity.MEDIUM]: 4,
          [NotificationSeverity.LOW]: 5,
        },
        by_type: {
          [NotificationType.INTERACTION_ALERT]: 3,
          [NotificationType.RISK_ALERT]: 2,
          [NotificationType.MEDICATION_REMINDER]: 4,
          [NotificationType.LAB_FOLLOWUP]: 1,
          [NotificationType.SYMPTOM_MONITORING]: 1,
          [NotificationType.GENERAL_INFO]: 1,
        },
      });
    }
  };

  // ✅ Memoized dummy notifications - only created once
  const generateDummyNotifications = useMemo(() => (): NotificationResponse[] => [
    {
      notification_id: '1',
      user_id: 'user1',
      title: 'Drug Interaction Alert',
      message: 'Potential interaction detected between Warfarin and Ibuprofen. This combination may increase bleeding risk.',
      notification_type: NotificationType.INTERACTION_ALERT,
      severity: NotificationSeverity.HIGH,
      is_read: false,
      created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      metadata: {
        correlation_type: 'drug_interaction',
        confidence_score: 0.85,
        recommendations: [
          'Consider alternative pain management',
          'Monitor for signs of bleeding',
          'Consult your doctor before taking both medications'
        ],
        related_entities: [
          { type: 'medication', id: 'med1', name: 'Warfarin' },
          { type: 'medication', id: 'med2', name: 'Ibuprofen' }
        ]
      }
    },
    {
      notification_id: '2',
      user_id: 'user1',
      title: 'Medication Reminder',
      message: 'Time to take your evening Metformin (500mg). Don\'t forget to take it with food.',
      notification_type: NotificationType.MEDICATION_REMINDER,
      severity: NotificationSeverity.MEDIUM,
      is_read: false,
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      metadata: {
        entity_type: 'medication',
        entity_id: 'med3',
        recommendations: ['Take with food', 'Set a daily reminder']
      }
    },
    {
      notification_id: '3',
      user_id: 'user1',
      title: 'Lab Result Follow-up',
      message: 'Your recent cholesterol levels are elevated (LDL: 160 mg/dL). Consider discussing treatment options with your doctor.',
      notification_type: NotificationType.LAB_FOLLOWUP,
      severity: NotificationSeverity.MEDIUM,
      is_read: true,
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      read_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      metadata: {
        correlation_type: 'lab_abnormal',
        confidence_score: 0.92,
        recommendations: [
          'Schedule follow-up appointment',
          'Consider dietary changes',
          'Discuss statin therapy options'
        ]
      }
    }
  ], []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    await Promise.all([fetchNotifications(), fetchStats()]);
    setRefreshing(false);
  };

  const retryOperation = () => {
    setCriticalError(null);
    setError(null);
    setLoading(true);
    fetchNotifications();
    fetchStats();
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      crashReporting.addBreadcrumb('Marking notification as read', 'user-action', 'info');

      await notificationServices.markNotificationsAsRead({
        notification_ids: [notificationId]
      });

      setNotifications(prev =>
        prev.map(n =>
          n.notification_id === notificationId
            ? { ...n, is_read: true, read_at: new Date().toISOString() }
            : n
        )
      );

      // Update stats
      if (stats) {
        setStats(prev => prev ? { ...prev, unread_count: prev.unread_count - 1 } : null);
      }
    } catch (markReadError: any) {
      console.error('Failed to mark notification as read:', markReadError);

      const errorMessage = markReadError.response?.data?.detail || 'Failed to mark notification as read. Please try again.';
      Alert.alert('Error', errorMessage);

      crashReporting.captureException(markReadError, {
        context: 'notification_mark_read',
        notificationId: notificationId,
        errorType: 'notification_update_error',
      });
    }
  };

  const handleDelete = async (notificationId: string) => {
    Alert.alert(
      'Delete Notification',
      'Are you sure you want to delete this notification?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await notificationServices.deleteNotification(notificationId);
              setNotifications(prev => prev.filter(n => n.notification_id !== notificationId));

              // Update stats
              if (stats) {
                const notification = notifications.find(n => n.notification_id === notificationId);
                setStats(prev => prev ? {
                  ...prev,
                  total_count: prev.total_count - 1,
                  unread_count: notification && !notification.is_read ? prev.unread_count - 1 : prev.unread_count
                } : null);
              }
            } catch (error) {
              console.error('Failed to delete notification:', error);
              Alert.alert('Error', 'Failed to delete notification');
            }
          }
        }
      ]
    );
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationServices.markAllNotificationsAsRead();
      setNotifications(prev =>
        prev.map(n => ({
          ...n,
          is_read: true,
          read_at: n.read_at || new Date().toISOString()
        }))
      );

      if (stats) {
        setStats(prev => prev ? { ...prev, unread_count: 0 } : null);
      }
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      Alert.alert('Error', 'Failed to mark all notifications as read');
    }
  };

  const renderNotification = ({ item }: { item: NotificationResponse }) => (
    <NotificationCard
      notification={item}
      onPress={() => {
        // Handle notification press - could navigate to related screen
        console.log('Notification pressed:', item.notification_id);
      }}
      onMarkAsRead={() => handleMarkAsRead(item.notification_id)}
      onDelete={() => handleDelete(item.notification_id)}
    />
  );

  const renderFilterButton = (option: FilterOption, isActive: boolean, onPress: () => void) => (
    <TouchableOpacity
      key={option.value || 'all'}
      style={[
        {
          paddingHorizontal: 12,
          paddingVertical: 6,
          borderRadius: 16,
          marginRight: 8,
          backgroundColor: isActive ? colors.accentPrimary : colors.backgroundSecondary,
          borderWidth: 1,
          borderColor: isActive ? colors.accentPrimary : colors.borderSubtle,
        }
      ]}
      onPress={onPress}
    >
      <StyledText
        variant="caption"
        style={{ color: isActive ? 'white' : colors.textSecondary }}
      >
        {option.label}
      </StyledText>
    </TouchableOpacity>
  );

  // Show critical error state if needed
  if (criticalError) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Notifications"
          message={criticalError}
          onRetry={retryOperation}
          retryLabel="Try Again"
        />
      </ScreenContainer>
    );
  }

  if (loading) {
    return (
      <ScreenContainer scrollable={false} withPadding={false}>
        <StyledView className="flex-1 justify-center items-center">
          <StyledText variant="body1" color="textSecondary">
            Loading notifications...
          </StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledView className="flex-1">
        {/* Header */}
        <StyledView className="px-4 py-6 border-b border-gray-200">
          <StyledView className="flex-row justify-between items-center mb-4">
            <StyledText variant="h2" className="font-bold">
              Notifications
            </StyledText>
            {stats && stats.unread_count > 0 && (
              <TouchableOpacity onPress={handleMarkAllAsRead}>
                <StyledText variant="body2" color="accentPrimary" className="font-medium">
                  Mark All Read
                </StyledText>
              </TouchableOpacity>
            )}
          </StyledView>

          {/* Stats */}
          {stats && (
            <StyledView className="flex-row justify-between mb-4">
              <StyledView className="items-center">
                <StyledText variant="h3" className="font-bold">
                  {stats.total_count}
                </StyledText>
                <StyledText variant="caption" color="textMuted">
                  Total
                </StyledText>
              </StyledView>
              <StyledView className="items-center">
                <StyledText variant="h3" className="font-bold" color="accentPrimary">
                  {stats.unread_count}
                </StyledText>
                <StyledText variant="caption" color="textMuted">
                  Unread
                </StyledText>
              </StyledView>
              <StyledView className="items-center">
                <StyledText variant="h3" className="font-bold" color="error">
                  {stats.by_severity[NotificationSeverity.CRITICAL] || 0}
                </StyledText>
                <StyledText variant="caption" color="textMuted">
                  Critical
                </StyledText>
              </StyledView>
            </StyledView>
          )}

          {/* Type Filters */}
          <StyledView className="mb-3">
            <StyledText variant="label" className="mb-2 font-medium">
              Filter by Type
            </StyledText>
            <FlatList
              horizontal
              showsHorizontalScrollIndicator={false}
              data={typeFilters}
              keyExtractor={(item) => item.value || 'all'}
              renderItem={({ item }) =>
                renderFilterButton(
                  item,
                  selectedFilter === item.value,
                  () => setSelectedFilter(item.value)
                )
              }
            />
          </StyledView>

          {/* Severity Filters */}
          <StyledView>
            <StyledText variant="label" className="mb-2 font-medium">
              Filter by Severity
            </StyledText>
            <FlatList
              horizontal
              showsHorizontalScrollIndicator={false}
              data={severityFilters}
              keyExtractor={(item) => item.value || 'all'}
              renderItem={({ item }) =>
                renderFilterButton(
                  item,
                  selectedSeverity === item.value,
                  () => setSelectedSeverity(item.value)
                )
              }
            />
          </StyledView>
        </StyledView>

        {/* Notifications List */}
        <FlatList
          data={notifications}
          keyExtractor={(item) => item.notification_id}
          renderItem={renderNotification}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
          }
          contentContainerStyle={{ padding: 16 }}
          ListEmptyComponent={
            <StyledView className="flex-1 justify-center items-center py-20">
              <Ionicons
                name="notifications-outline"
                size={64}
                color={colors.textMuted}
              />
              <StyledText variant="h4" color="textMuted" className="mt-4 mb-2">
                No notifications
              </StyledText>
              <StyledText variant="body2" color="textMuted" className="text-center">
                You're all caught up! New notifications will appear here.
              </StyledText>
            </StyledView>
          }
        />
      </StyledView>
    </ScreenContainer>
  );
};

export default NotificationScreen; 