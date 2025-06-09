import React from 'react';
import { ScrollView, Switch, View } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import { useTheme } from '../../theme';
import { useAuth } from '../../context/AuthContext';

const StyledScrollView = styled(ScrollView);
const StyledView = styled(View);

type SettingsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Settings'>;

interface SettingItem {
  id: string;
  label: string;
  iconName: string;
  navigateTo?: keyof MainAppStackParamList | null;
  action?: () => void;
  isDestructive?: boolean;
  isToggle?: boolean;
  value?: boolean;
}

const SettingsScreen = () => {
  const navigation = useNavigation<SettingsScreenNavigationProp>();
  const { colors } = useTheme();
  const { signOut } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(true);

  const handleLogout = async () => {
    console.log("Logging out...");
    try {
      await signOut();
    } catch (error) {
      console.error("Error during sign out:", error);
    }
  };

  const handleExportData = () => {
    console.log("Initiating data export...");
    alert("Data Export Initiated! (Placeholder)");
  };

  const accountSettings: SettingItem[] = [
    { 
      id: 'profile', 
      label: 'Edit Profile', 
      iconName: 'person-circle-outline', 
      action: () => alert('Navigate to Edit Profile') 
    },
    { 
      id: 'security', 
      label: 'Security & Privacy', 
      iconName: 'shield-checkmark-outline', 
      action: () => alert('Navigate to Security') 
    },
    { 
      id: 'notifications', 
      label: 'Notifications', 
      iconName: 'notifications-outline', 
      isToggle: true, 
      value: notificationsEnabled, 
      action: () => setNotificationsEnabled(v => !v) 
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
      action: () => alert('Navigate to Help Center') 
    },
    { 
      id: 'contact', 
      label: 'Contact Support', 
      iconName: 'mail-outline', 
      action: () => alert('Open email to support') 
    },
    { 
      id: 'terms', 
      label: 'Terms of Service', 
      iconName: 'document-text-outline', 
      action: () => alert('Navigate to Terms') 
    },
    { 
      id: 'privacy', 
      label: 'Privacy Policy', 
      iconName: 'lock-closed-outline', 
      action: () => alert('Navigate to Privacy Policy') 
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
            <StyledText variant="body1" tw="flex-1">
              {item.label}
            </StyledText>
          </StyledView>
          <Switch 
            value={item.value} 
            onValueChange={item.action} 
            trackColor={{ false: colors.borderSubtle, true: colors.accentPrimary }}
            thumbColor={colors.backgroundSecondary}
          />
          {!isLastInSection && <StyledView className="absolute bottom-0 left-12 right-0 h-px bg-gray-200" />}
        </StyledView>
      );
    }

    return (
      <ListItem
        key={item.id}
        label={item.label}
        iconLeft={item.iconName}
        iconLeftColor={item.isDestructive ? colors.error : colors.textSecondary}
        labelStyle={item.isDestructive ? { color: colors.error } : {}}
        onPress={item.action}
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
          <StyledText variant="h1" tw="font-bold text-3xl">
            Settings
          </StyledText>
        </StyledView>

        {/* Account Section */}
        <StyledView className="mt-6">
          <StyledText variant="h4" tw="px-4 pb-2 font-semibold text-gray-600 uppercase text-sm">
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
          <StyledText variant="h4" tw="px-4 pb-2 font-semibold text-gray-600 uppercase text-sm">
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
          <StyledText variant="h4" tw="px-4 pb-2 font-semibold text-gray-600 uppercase text-sm">
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
