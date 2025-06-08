import React from 'react';
import { ScrollView, Switch, View } from 'react-native'; // Added View for StyledView
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import { useTheme } from '../../theme';
import { useAuth } from '../../context/AuthContext'; // Import useAuth

const StyledScrollView = styled(ScrollView);
const StyledView = styled(View);

type SettingsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Settings'>;

// Define a type for our settings items
interface SettingItem {
  id: string;
  label: string;
  iconName: string;
  navigateTo?: keyof MainAppStackParamList | null; // Or a specific settings sub-screen type
  action?: () => void;
  isDestructive?: boolean;
  isToggle?: boolean; // For future switch integration
  value?: boolean;    // For future switch integration
}

const SettingsScreen = () => {
  const navigation = useNavigation<SettingsScreenNavigationProp>();
  const { colors } = useTheme();
  const { signOut } = useAuth(); // Get signOut from context
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(true); // Example state for a toggle

  const handleLogout = async () => { // Make it async
    console.log("Logging out...");
    try {
      await signOut(); // Call the actual signOut function
      // The onAuthStateChange listener in AuthContext should handle navigation implicitly
      // by updating the session state, which AppNavigator listens to.
    } catch (error) {
      console.error("Error during sign out:", error);
      // Optionally, show an alert to the user
    }
  };

  const handleExportData = () => {
    console.log("Initiating data export...");
    alert("Data Export Initiated! (Placeholder)");
  };

  const accountSettings: SettingItem[] = [
    { id: 'profile', label: 'Edit Profile', iconName: 'person-circle-outline', navigateTo: null /* TODO: Add ProfileEditScreen */, action: () => alert('Navigate to Edit Profile') },
    { id: 'security', label: 'Security & Privacy', iconName: 'shield-checkmark-outline', navigateTo: null, action: () => alert('Navigate to Security') },
    { id: 'notifications', label: 'Notifications', iconName: 'notifications-outline', isToggle: true, value: notificationsEnabled, action: () => setNotificationsEnabled(v => !v) },
  ];

  const dataSettings: SettingItem[] = [
    { id: 'export', label: 'Export My Data', iconName: 'download-outline', action: handleExportData },
    // { id: 'storage', label: 'Manage Storage', iconName: 'folder-open-outline', navigateTo: null, action: () => alert('Navigate to Storage Mgmt') },
  ];
  
  const aboutSettings: SettingItem[] = [
    { id: 'help', label: 'Help Center', iconName: 'help-circle-outline', action: () => alert('Navigate to Help Center') },
    { id: 'contact', label: 'Contact Support', iconName: 'mail-outline', action: () => alert('Open email to support') },
    { id: 'terms', label: 'Terms of Service', iconName: 'document-text-outline', action: () => alert('Navigate to Terms') },
    { id: 'privacy', label: 'Privacy Policy', iconName: 'lock-closed-outline', action: () => alert('Navigate to Privacy Policy') },
  ];

  const renderSettingItem = (item: SettingItem, isLastInSection: boolean) => (
    <ListItem
      key={item.id}
      label={item.label}
      iconLeft={item.iconName}
      iconLeftColor={item.isDestructive ? colors.accentDestructive : colors.textSecondary}
      labelStyle={item.isDestructive ? { color: colors.accentDestructive } : {}}
      onPress={item.navigateTo ? () => navigation.navigate(item.navigateTo as any) : item.action}
      showBottomBorder={!isLastInSection}
      // For toggles, we'd render a Switch component as children or in place of iconRight
      iconRight={item.isToggle ? undefined : (item.navigateTo || item.action) ? 'chevron-forward-outline' : undefined}
    >
      {item.isToggle ? (
        <StyledView>
          <Switch 
            value={item.value} 
            onValueChange={item.action} 
            trackColor={{ false: colors.borderSubtle, true: colors.accentPrimary }}
            thumbColor={item.value ? colors.backgroundSecondary : colors.backgroundSecondary}
          />
        </StyledView>
      ) : null}
    </ListItem>
  );

  return (
    // Using backgroundTertiary for the main screen for an iOS settings feel
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundTertiary}>
      <StyledScrollView className="flex-1">
        <StyledText variant="h1" tw="px-4 pt-6 pb-4 font-bold">Settings</StyledText>

        <Card title="Account" tw="mx-4 mb-6" noPadding> {/* noPadding on Card, ListItem will handle internal padding/borders */}
          {accountSettings.map((item, index) => renderSettingItem(item, index === accountSettings.length - 1))}
        </Card>

        <Card title="Data Management" tw="mx-4 mb-6" noPadding>
          {dataSettings.map((item, index) => renderSettingItem(item, index === dataSettings.length - 1))}
        </Card>

        <Card title="About" tw="mx-4 mb-6" noPadding>
          {aboutSettings.map((item, index) => renderSettingItem(item, index === aboutSettings.length - 1))}
          <ListItem 
            label="App Version: 1.0.0"
            iconLeft="information-circle-outline"
            iconLeftColor={colors.textSecondary}
            showBottomBorder={false} 
          />
        </Card>
        
        <StyledView tw="mx-4 mb-6">
            <ListItem
                label="Log Out"
                iconLeft="log-out-outline"
                iconLeftColor={colors.accentDestructive}
                labelStyle={{ color: colors.accentDestructive }}
                onPress={handleLogout} // This now calls the corrected handleLogout
                showBottomBorder={false}
                tw="bg-backgroundSecondary rounded-lg px-4"
             />
        </StyledView>

      </StyledScrollView>
    </ScreenContainer>
  );
};

export default SettingsScreen;
