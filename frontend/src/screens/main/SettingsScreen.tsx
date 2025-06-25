import React from 'react';
import { ScrollView, View, Alert, Switch } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import ListItem from '../../components/common/ListItem';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import { supabaseClient } from '../../services/supabase';
import { MainAppStackParamList } from '../../navigation/types';
import { ERROR_MESSAGES } from '../../constants/messages';
import { SettingItem } from '../../types/interfaces';
import { crashReporting } from '../../services/crashReporting';

const StyledScrollView = styled(ScrollView);
const StyledView = styled(View);

type SettingsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Settings'>;

const SettingsScreen = () => {
  const navigation = useNavigation<SettingsScreenNavigationProp>();
  const { colors } = useTheme();
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(true);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [criticalError, setCriticalError] = React.useState<string | null>(null);

  const handleLogout = async () => {
    Alert.alert(
      'Log Out',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Log Out',
          style: 'destructive',
          onPress: performLogout
        }
      ]
    );
  };

  const performLogout = async () => {
    setLoading(true);
    setError(null);

    try {
      crashReporting.addBreadcrumb('User initiated logout', 'user-action', 'info');

      const { error: signOutError } = await supabaseClient.auth.signOut();

      if (signOutError) {
        console.error("Error during sign out:", signOutError);
        setError(ERROR_MESSAGES.LOGOUT_ERROR);
        crashReporting.captureException(new Error(signOutError.message), {
          context: 'settings_logout',
          errorType: 'auth_signout_error',
        });
      }
    } catch (catchError: any) {
      console.error("Unexpected error during sign out:", catchError);
      setError(ERROR_MESSAGES.LOGOUT_ERROR);
      crashReporting.captureException(catchError, {
        context: 'settings_logout',
        errorType: 'unexpected_logout_error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setLoading(true);
    setError(null);

    try {
      crashReporting.addBreadcrumb('User requested data export', 'user-action', 'info');

      // Simulate data export process
      await new Promise(resolve => setTimeout(resolve, 2000));

      Alert.alert(
        'Export Initiated',
        'Your data export has been initiated. You will receive an email with download instructions within 24 hours.',
        [{ text: 'OK' }]
      );
    } catch (exportError: any) {
      console.error("Error during data export:", exportError);
      setError('Failed to initiate data export. Please try again.');
      crashReporting.captureException(exportError, {
        context: 'settings_data_export',
        errorType: 'data_export_error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationToggle = async (enabled: boolean) => {
    setLoading(true);
    setError(null);

    try {
      // Simulate notification settings update
      await new Promise(resolve => setTimeout(resolve, 500));

      setNotificationsEnabled(enabled);
      crashReporting.addBreadcrumb(
        `Notifications ${enabled ? 'enabled' : 'disabled'}`,
        'user-action',
        'info'
      );
    } catch (notificationError: any) {
      console.error("Error updating notification settings:", notificationError);
      setError('Failed to update notification settings. Please try again.');
      crashReporting.captureException(notificationError, {
        context: 'settings_notifications',
        errorType: 'notification_settings_error',
      });
    } finally {
      setLoading(false);
    }
  };

  const retryOperation = () => {
    setCriticalError(null);
    setError(null);
  };

  // Show critical error state if needed
  if (criticalError) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Settings Error"
          message={criticalError}
          onRetry={retryOperation}
          retryLabel="Try Again"
        />
      </ScreenContainer>
    );
  }

  const accountSettings: SettingItem[] = [
    {
      id: 'profile',
      label: 'Edit Profile',
      iconName: 'person-circle-outline',
      navigateTo: 'EditProfile'
    },
    {
      id: 'security',
      label: 'Security & Privacy',
      iconName: 'shield-checkmark-outline',
      action: () => Alert.alert('Coming Soon', 'Security settings will be available in a future update.')
    },
    {
      id: 'notifications',
      label: 'Notifications',
      iconName: 'notifications-outline',
      isToggle: true,
      value: notificationsEnabled,
      action: () => handleNotificationToggle(!notificationsEnabled)
    },
  ];

  const dataSettings: SettingItem[] = [
    {
      id: 'export',
      label: 'Export My Data',
      iconName: 'download-outline',
      action: handleExportData
    },
  ];

  const aboutSettings: SettingItem[] = [
    {
      id: 'help',
      label: 'Help Center',
      iconName: 'help-circle-outline',
      action: () => Alert.alert('Help Center', 'Help documentation will be available soon.')
    },
    {
      id: 'contact',
      label: 'Contact Support',
      iconName: 'mail-outline',
      action: () => Alert.alert('Contact Support', 'Support contact information will be available soon.')
    },
    {
      id: 'terms',
      label: 'Terms of Service',
      iconName: 'document-text-outline',
      action: () => Alert.alert('Terms of Service', 'Terms of service will be available soon.')
    },
    {
      id: 'privacy',
      label: 'Privacy Policy',
      iconName: 'lock-closed-outline',
      action: () => Alert.alert('Privacy Policy', 'Privacy policy will be available soon.')
    },
  ];

  const renderSettingItem = (item: SettingItem, isLastInSection: boolean) => {
    if (item.isToggle) {
      return (
        <StyledView key={item.id} className="flex-row items-center justify-between px-4 py-3 bg-white">
          <StyledView className="flex-row items-center flex-1">
            <StyledView className="w-6 h-6 items-center justify-center mr-3">
              <Ionicons name={item.iconName as any} size={22} color={colors.textSecondary} />
            </StyledView>
            <StyledText variant="body1" className="flex-1">
              {item.label}
            </StyledText>
          </StyledView>
          <Switch
            value={item.value}
            onValueChange={item.action}
            trackColor={{ false: colors.borderSubtle, true: colors.accentPrimary }}
            thumbColor={colors.backgroundSecondary}
            disabled={loading}
          />
          {!isLastInSection && <StyledView className="absolute bottom-0 left-12 right-0 h-px bg-gray-200" />}
        </StyledView>
      );
    }

    const handlePress = () => {
      if (loading) return; // Prevent actions while loading

      if (item.navigateTo) {
        navigation.navigate(item.navigateTo);
      } else if (item.action) {
        item.action();
      }
    };

    return (
      <ListItem
        key={item.id}
        label={item.label}
        iconLeft={item.iconName}
        iconLeftColor={item.isDestructive ? colors.error : colors.textSecondary}
        labelStyle={item.isDestructive ? { color: colors.error } : {}}
        onPress={handlePress}
        showBottomBorder={!isLastInSection}
        iconRight="chevron-forward-outline"
      />
    );
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledScrollView className="flex-1 bg-gray-50">
        {/* Header */}
        <StyledView className="px-4 pt-12 pb-6 bg-white">
          <StyledText variant="h1" className="font-bold text-3xl">
            Settings
          </StyledText>
          {error && (
            <StyledView className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
              <StyledText variant="caption" color="error" className="text-center">
                {error}
              </StyledText>
            </StyledView>
          )}
        </StyledView>

        {/* Account Section */}
        <StyledView className="mt-6">
          <StyledText variant="h4" className="px-4 pb-2 font-semibold text-gray-600 uppercase text-sm">
            Account
          </StyledText>
          <StyledView className="bg-white mx-4 rounded-lg overflow-hidden">
            {accountSettings.map((item, index) =>
              renderSettingItem(item, index === accountSettings.length - 1)
            )}
          </StyledView>
        </StyledView>

        {/* Data Management Section */}
        <StyledView className="mt-6">
          <StyledText variant="h4" className="px-4 pb-2 font-semibold text-gray-600 uppercase text-sm">
            Data Management
          </StyledText>
          <StyledView className="bg-white mx-4 rounded-lg overflow-hidden">
            {dataSettings.map((item, index) =>
              renderSettingItem(item, index === dataSettings.length - 1)
            )}
          </StyledView>
        </StyledView>

        {/* About Section */}
        <StyledView className="mt-6">
          <StyledText variant="h4" className="px-4 pb-2 font-semibold text-gray-600 uppercase text-sm">
            About
          </StyledText>
          <StyledView className="bg-white mx-4 rounded-lg overflow-hidden">
            {aboutSettings.map((item, index) =>
              renderSettingItem(item, index === aboutSettings.length - 1)
            )}

            {/* App Version */}
            <StyledView className="flex-row items-center px-4 py-3">
              <StyledView className="w-6 h-6 items-center justify-center mr-3">
                <Ionicons name="information-circle-outline" size={22} color={colors.textSecondary} />
              </StyledView>
              <StyledText variant="body1" color="textSecondary">
                App Version: 1.0.0
              </StyledText>
            </StyledView>
          </StyledView>
        </StyledView>

        {/* Logout Button */}
        <StyledView className="mt-6 mx-4 mb-8">
          <StyledView className="bg-white rounded-lg overflow-hidden">
            <ListItem
              label="Log Out"
              iconLeft="log-out-outline"
              iconLeftColor={colors.error}
              labelStyle={{ color: colors.error, fontWeight: '600' }}
              onPress={handleLogout}
              showBottomBorder={false}
            />
          </StyledView>
        </StyledView>

      </StyledScrollView>
    </ScreenContainer>
  );
};

export default SettingsScreen;
