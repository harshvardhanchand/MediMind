import React, { useState } from 'react';
import { View, TouchableOpacity, Modal, FlatList, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';

import StyledText from './StyledText';
import StyledButton from './StyledButton';
import { useTheme } from '../../theme';
import { useNotifications } from '../../context/NotificationContext';
import { notificationServices } from '../../api/services';
import { NotificationResponse } from '../../types/api';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledModal = styled(Modal);

interface HeaderNotificationsProps {
  onPress?: () => void;
}

const HeaderNotifications: React.FC<HeaderNotificationsProps> = ({ onPress }) => {
  const { colors } = useTheme();
  const navigation = useNavigation<any>();
  const { unreadCount } = useNotifications();
  const [isDropdownVisible, setIsDropdownVisible] = useState(false);
  const [recentNotifications, setRecentNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const handleBellPress = async () => {
    if (onPress) {
      onPress();
      return;
    }

    // Fetch recent notifications for dropdown
    setLoading(true);
    try {
      const response = await notificationServices.getNotifications({ limit: 5 });
      
      // If API returns empty, use dummy data for demo
      if (response.data && response.data.length > 0) {
        setRecentNotifications(response.data);
      } else {
        setRecentNotifications(generateDummyNotifications());
      }
    } catch (error) {
      console.error('Failed to fetch recent notifications:', error);
      setRecentNotifications(generateDummyNotifications());
    } finally {
      setLoading(false);
      setIsDropdownVisible(true);
    }
  };

  const generateDummyNotifications = (): NotificationResponse[] => [
    {
      notification_id: '1',
      user_id: 'user1',
      title: 'Drug Interaction Alert',
      message: 'Potential interaction detected between Warfarin and Ibuprofen.',
      notification_type: 'interaction_alert' as any,
      severity: 'high' as any,
      is_read: false,
      created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    },
    {
      notification_id: '2',
      user_id: 'user1',
      title: 'Medication Reminder',
      message: 'Time to take your evening Metformin (500mg).',
      notification_type: 'medication_reminder' as any,
      severity: 'medium' as any,
      is_read: false,
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      notification_id: '3',
      user_id: 'user1',
      title: 'Lab Result Follow-up',
      message: 'Your recent cholesterol levels are elevated.',
      notification_type: 'lab_followup' as any,
      severity: 'medium' as any,
      is_read: true,
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    }
  ];

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationServices.markNotificationsAsRead({ 
        notification_ids: [notificationId] 
      });
      
      setRecentNotifications(prev => 
        prev.map(n => 
          n.notification_id === notificationId 
            ? { ...n, is_read: true, read_at: new Date().toISOString() }
            : n
        )
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleViewAll = () => {
    setIsDropdownVisible(false);
    navigation.navigate('NotificationScreen');
  };

  const renderNotificationItem = ({ item }: { item: NotificationResponse }) => (
    <StyledView className="px-4 py-3 border-b border-gray-100">
      <StyledView className="flex-row justify-between items-start mb-1">
        <StyledText variant="body2" tw="font-medium flex-1 mr-2" numberOfLines={1}>
          {item.title}
        </StyledText>
        <StyledView className="flex-row items-center">
          {!item.is_read && (
            <StyledView 
              className="w-2 h-2 rounded-full mr-2"
              style={{ backgroundColor: colors.accentPrimary }}
            />
          )}
          <StyledText variant="caption" color="textMuted">
            {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </StyledText>
        </StyledView>
      </StyledView>
      
      <StyledText variant="caption" color="textSecondary" numberOfLines={2} tw="mb-2">
        {item.message}
      </StyledText>
      
      {!item.is_read && (
        <StyledTouchableOpacity onPress={() => handleMarkAsRead(item.notification_id)}>
          <StyledText variant="caption" color="accentPrimary" tw="font-medium">
            Mark as read
          </StyledText>
        </StyledTouchableOpacity>
      )}
    </StyledView>
  );

  return (
    <>
      <StyledTouchableOpacity 
        onPress={handleBellPress}
        className="relative p-2"
        style={{ marginRight: -8 }} // Adjust positioning
      >
        <Ionicons 
          name="notifications-outline" 
          size={24} 
          color={colors.textPrimary} 
        />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <StyledView 
            className="absolute -top-1 -right-1 min-w-[18px] h-[18px] rounded-full items-center justify-center"
            style={{ backgroundColor: colors.error }}
          >
            <StyledText 
              variant="caption" 
              tw="text-white text-xs font-bold"
              style={{ fontSize: 10 }}
            >
              {unreadCount > 99 ? '99+' : unreadCount.toString()}
            </StyledText>
          </StyledView>
        )}
      </StyledTouchableOpacity>

      {/* Notification Dropdown Modal */}
      <StyledModal
        visible={isDropdownVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIsDropdownVisible(false)}
      >
        <Pressable 
          style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.3)' }}
          onPress={() => setIsDropdownVisible(false)}
        >
          <StyledView className="flex-1 justify-start items-end pt-16 pr-4">
            <StyledView 
              className="w-80 max-h-96 rounded-lg shadow-lg"
              style={{ backgroundColor: colors.backgroundPrimary }}
            >
              {/* Header */}
              <StyledView className="px-4 py-3 border-b border-gray-200">
                <StyledView className="flex-row justify-between items-center">
                  <StyledText variant="h4" tw="font-semibold">
                    Notifications
                  </StyledText>
                  <StyledTouchableOpacity onPress={() => setIsDropdownVisible(false)}>
                    <Ionicons name="close" size={20} color={colors.textSecondary} />
                  </StyledTouchableOpacity>
                </StyledView>
              </StyledView>

              {/* Notifications List */}
              {loading ? (
                <StyledView className="p-8 items-center">
                  <StyledText variant="body2" color="textSecondary">
                    Loading notifications...
                  </StyledText>
                </StyledView>
              ) : recentNotifications.length > 0 ? (
                <>
                  <FlatList
                    data={recentNotifications}
                    keyExtractor={(item) => item.notification_id}
                    renderItem={renderNotificationItem}
                    style={{ maxHeight: 250 }}
                    showsVerticalScrollIndicator={false}
                  />
                  
                  {/* Footer */}
                  <StyledView className="p-3 border-t border-gray-200">
                    <StyledButton
                      variant="textPrimary"
                      onPress={handleViewAll}
                      tw="w-full"
                    >
                      View All Notifications
                    </StyledButton>
                  </StyledView>
                </>
              ) : (
                <StyledView className="p-8 items-center">
                  <Ionicons 
                    name="notifications-outline" 
                    size={32} 
                    color={colors.textMuted} 
                  />
                  <StyledText variant="body2" color="textMuted" tw="mt-2 text-center">
                    No notifications
                  </StyledText>
                </StyledView>
              )}
            </StyledView>
          </StyledView>
        </Pressable>
      </StyledModal>
    </>
  );
};

export default HeaderNotifications; 