import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';


// Import your screens
import DocumentsScreen from '../screens/main/DocumentsScreen';
import HealthDataScreen from '../screens/main/HealthDataScreen'; // The placeholder we created
import AssistantScreen from '../screens/main/AssistantScreen';
import SettingsScreen from '../screens/main/SettingsScreen';
import { colors } from '../theme/colors'; // Your new color palette

import DashboardStackNavigator from './DashboardStackNavigator'; // Import the new stack navigator

// Define ParamList for the Tab Navigator
export type MainBottomTabParamList = {
  DashboardTab: undefined; // Changed from Dashboard to avoid conflict with potential stack screen name
  DocumentsTab: undefined;
  DataTab: undefined;
  AssistantTab: undefined;
  SettingsTab: undefined;
};

const Tab = createBottomTabNavigator<MainBottomTabParamList>();

const MainTabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'home-outline';

          if (route.name === 'DashboardTab') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'DocumentsTab') {
            iconName = focused ? 'documents' : 'documents-outline';
          } else if (route.name === 'DataTab') {
            iconName = focused ? 'bar-chart' : 'bar-chart-outline';
          } else if (route.name === 'AssistantTab') {
            iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
          } else if (route.name === 'SettingsTab') {
            iconName = focused ? 'settings' : 'settings-outline';
          }
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
      })}
    >
      <Tab.Screen 
        name="DashboardTab" 
        component={DashboardStackNavigator}
        options={{ tabBarLabel: 'Dashboard' }}
      />
      <Tab.Screen 
        name="DocumentsTab" 
        component={DocumentsScreen} 
        options={{ tabBarLabel: 'Documents' }}
      />
      <Tab.Screen 
        name="DataTab" 
        component={HealthDataScreen} 
        options={{ tabBarLabel: 'Data' }}
      />
      <Tab.Screen 
        name="AssistantTab" 
        component={AssistantScreen} 
        options={{ tabBarLabel: 'Assistant' }}
      />
      <Tab.Screen 
        name="SettingsTab" 
        component={SettingsScreen} 
        options={{ tabBarLabel: 'Settings' }}
      />
    </Tab.Navigator>
  );
};

export default MainTabNavigator; 