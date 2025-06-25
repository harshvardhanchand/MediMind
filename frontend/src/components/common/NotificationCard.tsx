import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../theme/colors';
import { NotificationResponse, NotificationType, NotificationSeverity } from '../../types/api';
import StyledText from './StyledText';

interface NotificationCardProps {
  notification: NotificationResponse;
  onPress?: () => void;
  onMarkAsRead?: () => void;
  onDelete?: () => void;
  showActions?: boolean;
}

const NotificationCard: React.FC<NotificationCardProps> = ({
  notification,
  onPress,
  onMarkAsRead,
  onDelete,
  showActions = true,
}) => {
  const getSeverityColor = (severity: NotificationSeverity) => {
    switch (severity) {
      case NotificationSeverity.CRITICAL:
        return colors.error;
      case NotificationSeverity.HIGH:
        return colors.warning;
      case NotificationSeverity.MEDIUM:
        return colors.info;
      case NotificationSeverity.LOW:
      default:
        return colors.textSecondary;
    }
  };

  const getTypeIcon = (type: NotificationType) => {
    switch (type) {
      case NotificationType.INTERACTION_ALERT:
        return 'warning-outline';
      case NotificationType.RISK_ALERT:
        return 'alert-circle-outline';
      case NotificationType.MEDICATION_REMINDER:
        return 'medical-outline';
      case NotificationType.LAB_FOLLOWUP:
        return 'flask-outline';
      case NotificationType.SYMPTOM_MONITORING:
        return 'pulse-outline';
      case NotificationType.GENERAL_INFO:
      default:
        return 'information-circle-outline';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInDays < 7) return `${diffInDays}d ago`;

    return date.toLocaleDateString();
  };

  return (
    <TouchableOpacity
      style={[
        styles.container,
        !notification.is_read && styles.unreadContainer
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Ionicons
            name={getTypeIcon(notification.notification_type)}
            size={24}
            color={getSeverityColor(notification.severity)}
          />
        </View>

        <View style={styles.headerText}>
          <StyledText variant="label" tw="font-semibold" numberOfLines={1}>
            {notification.title}
          </StyledText>
          <StyledText variant="caption" color="textMuted">
            {formatDate(notification.created_at)}
          </StyledText>
        </View>

        {!notification.is_read && (
          <View style={styles.unreadDot} />
        )}
      </View>

      <StyledText
        variant="body2"
        color="textSecondary"
        tw="mt-2"
        numberOfLines={3}
      >
        {notification.message}
      </StyledText>

      {notification.metadata?.recommendations && (
        <View style={styles.recommendations}>
          <StyledText variant="caption" color="textMuted" tw="mb-1">
            Recommendations:
          </StyledText>
          {notification.metadata.recommendations.slice(0, 2).map((rec, index) => (
            <StyledText key={index} variant="caption" color="textSecondary" tw="ml-2">
              • {rec}
            </StyledText>
          ))}
        </View>
      )}

      {showActions && (
        <View style={styles.actions}>
          {!notification.is_read && onMarkAsRead && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={(e) => {
                e.stopPropagation();
                onMarkAsRead();
              }}
            >
              <Ionicons name="checkmark-outline" size={16} color={colors.success} />
              <StyledText variant="caption" color="success" tw="ml-1">
                Mark Read
              </StyledText>
            </TouchableOpacity>
          )}

          {onDelete && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              <Ionicons name="trash-outline" size={16} color={colors.error} />
              <StyledText variant="caption" color="error" tw="ml-1">
                Delete
              </StyledText>
            </TouchableOpacity>
          )}
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.backgroundSecondary,
    borderRadius: 12,
    padding: 16,
    marginVertical: 4,
    borderLeftWidth: 4,
    borderLeftColor: colors.borderSubtle,
  },
  unreadContainer: {
    backgroundColor: colors.backgroundPrimary,
    borderLeftColor: colors.accentPrimary,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconContainer: {
    marginRight: 12,
    marginTop: 2,
  },
  headerText: {
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.accentPrimary,
    marginLeft: 8,
    marginTop: 4,
  },
  recommendations: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 8,
    marginLeft: 12,
  },
});

export default NotificationCard; 