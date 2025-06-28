import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { BottomTabNavigationOptions } from '@react-navigation/bottom-tabs';

import DocumentsScreen from '../screens/main/DocumentsScreen';
import HealthDataScreen from '../screens/main/HealthDataScreen';
import AssistantScreen from '../screens/main/AssistantScreen';
import SettingsScreen from '../screens/main/SettingsScreen';
import { colors } from '../theme/colors';
import DashboardStackNavigator from './DashboardStackNavigator';
import { withScreenErrorBoundary } from '../utils/withErrorBoundary';

// Define ParamList for the Tab Navigator
export type MainBottomTabParamList = {
  DashboardTab: undefined;
  DocumentsTab: undefined;
  DataTab: undefined;
  AssistantTab: undefined;
  SettingsTab: undefined;
};

// Icon mapping to eliminate if/else chain
const TAB_ICONS = {
  DashboardTab: { outline: 'home-outline', filled: 'home' },
  DocumentsTab: { outline: 'document-outline', filled: 'document' },
  DataTab: { outline: 'bar-chart-outline', filled: 'bar-chart' },
  AssistantTab: { outline: 'chatbubble-outline', filled: 'chatbubble' },
  SettingsTab: { outline: 'settings-outline', filled: 'settings' },
} as const;

// Helper function to get icon name
const getTabIcon = (routeName: keyof MainBottomTabParamList, focused: boolean): keyof typeof Ionicons.glyphMap => {
  const icons = TAB_ICONS[routeName];
  return focused ? icons.filled : icons.outline;
};

// Create wrapped components with error boundaries (stable references)
const DocumentsScreenWithBoundary = withScreenErrorBoundary(DocumentsScreen, 'DocumentsScreen');
const HealthDataScreenWithBoundary = withScreenErrorBoundary(HealthDataScreen, 'HealthDataScreen');
const AssistantScreenWithBoundary = withScreenErrorBoundary(AssistantScreen, 'AssistantScreen');
const SettingsScreenWithBoundary = withScreenErrorBoundary(SettingsScreen, 'SettingsScreen');

// Extract screenOptions to avoid creating new object on each render
const screenOptions = ({ route }: { route: { name: keyof MainBottomTabParamList } }): BottomTabNavigationOptions => ({
  tabBarIcon: ({ focused, color, size }) => {
    const iconName = getTabIcon(route.name, focused);
    return <Ionicons name={iconName} size={size} color={color} />;
  },
  tabBarActiveTintColor: colors.accentPrimary,
  tabBarInactiveTintColor: colors.textSecondary,
  tabBarStyle: {
    backgroundColor: colors.backgroundSecondary,
    borderTopColor: colors.borderSubtle,
  },
  headerShown: false,
  tabBarLabelStyle: {
    fontSize: 10,
  },
});

const Tab = createBottomTabNavigator<MainBottomTabParamList>();

const MainTabNavigator = () => {
  return (
    <Tab.Navigator screenOptions={screenOptions}>
      <Tab.Screen
        name="DashboardTab"
        component={DashboardStackNavigator}
        options={{ tabBarLabel: 'Dashboard' }}
      />
      <Tab.Screen
        name="DocumentsTab"
        component={DocumentsScreenWithBoundary}
        options={{ tabBarLabel: 'Documents' }}
      />
      <Tab.Screen
        name="DataTab"
        component={HealthDataScreenWithBoundary}
        options={{ tabBarLabel: 'Data' }}
      />
      <Tab.Screen
        name="AssistantTab"
        component={AssistantScreenWithBoundary}
        options={{ tabBarLabel: 'Assistant' }}
      />
      <Tab.Screen
        name="SettingsTab"
        component={SettingsScreenWithBoundary}
        options={{ tabBarLabel: 'Settings' }}
      />
    </Tab.Navigator>
  );
};

export default MainTabNavigator; 