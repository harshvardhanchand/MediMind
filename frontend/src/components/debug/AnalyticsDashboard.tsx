import React, { useState, useEffect } from 'react';
import { View, ScrollView, Alert } from 'react-native';
import { analytics } from '../../services/analytics';
import { useTheme } from '../../theme';
import StyledText from '../common/StyledText';
import StyledButton from '../common/StyledButton';

interface RetentionData {
  total_sessions: number;
  first_open: number;
  last_open: number;
  unique_days: number;
}

const AnalyticsDashboard: React.FC = () => {
  const theme = useTheme();
  const [retentionData, setRetentionData] = useState<RetentionData | null>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      const retention = await analytics.getRetentionData();
      const events = await analytics.exportData();

      setRetentionData(retention);
      // Show last 10 events
      setRecentEvents(events.slice(-10).reverse());
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    }
  };

  const exportData = async () => {
    try {
      const data = await analytics.exportData();
      console.log('Analytics Data Export:', JSON.stringify(data, null, 2));
      Alert.alert(
        'Data Exported',
        `${data.length} events exported to console. Check your development console.`
      );
    } catch (error) {
      Alert.alert('Export Failed', 'Failed to export analytics data');
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString() + ' ' +
      new Date(timestamp).toLocaleTimeString();
  };

  const calculateDaysSince = (timestamp: number) => {
    const days = Math.floor((Date.now() - timestamp) / (1000 * 60 * 60 * 24));
    return days === 0 ? 'Today' : `${days} days ago`;
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.backgroundPrimary }}>
      <View style={{ padding: 20 }}>
        <StyledText variant="h2" style={{ marginBottom: 20, textAlign: 'center' }}>
          Analytics Dashboard
        </StyledText>

        {/* Retention Metrics */}
        <View style={{
          backgroundColor: theme.colors.backgroundSecondary,
          padding: 15,
          borderRadius: 10,
          marginBottom: 20
        }}>
          <StyledText variant="h3" style={{ marginBottom: 10 }}>
            Retention Metrics
          </StyledText>

          {retentionData ? (
            <>
              <StyledText style={{ marginBottom: 5 }}>
                Total Sessions: {retentionData.total_sessions}
              </StyledText>
              <StyledText style={{ marginBottom: 5 }}>
                Active Days: {retentionData.unique_days}
              </StyledText>
              <StyledText style={{ marginBottom: 5 }}>
                First Open: {retentionData.first_open ? formatDate(retentionData.first_open) : 'N/A'}
              </StyledText>
              <StyledText style={{ marginBottom: 5 }}>
                Last Open: {retentionData.last_open ? calculateDaysSince(retentionData.last_open) : 'N/A'}
              </StyledText>
              <StyledText style={{ marginBottom: 5 }}>
                Avg Sessions/Day: {retentionData.unique_days > 0 ?
                  (retentionData.total_sessions / retentionData.unique_days).toFixed(1) : '0'}
              </StyledText>
            </>
          ) : (
            <StyledText>No retention data available</StyledText>
          )}
        </View>

        {/* Recent Events */}
        <View style={{
          backgroundColor: theme.colors.backgroundSecondary,
          padding: 15,
          borderRadius: 10,
          marginBottom: 20
        }}>
          <StyledText variant="h3" style={{ marginBottom: 10 }}>
            Recent Events
          </StyledText>

          {recentEvents.length > 0 ? (
            recentEvents.map((event, index) => (
              <View key={index} style={{
                marginBottom: 10,
                padding: 10,
                backgroundColor: theme.colors.backgroundPrimary,
                borderRadius: 5
              }}>
                <StyledText variant="body2" style={{ fontWeight: 'bold' }}>
                  {event.event}
                </StyledText>
                <StyledText variant="caption">
                  {formatDate(event.timestamp)}
                </StyledText>
                {event.properties && (
                  <StyledText variant="caption" style={{ marginTop: 5 }}>
                    {JSON.stringify(event.properties, null, 2)}
                  </StyledText>
                )}
              </View>
            ))
          ) : (
            <StyledText>No recent events</StyledText>
          )}
        </View>

        {/* Actions */}
        <View style={{ gap: 10 }}>
          <StyledButton
            variant="filledPrimary"
            onPress={loadAnalyticsData}
          >
            Refresh Data
          </StyledButton>

          <StyledButton
            variant="textPrimary"
            onPress={exportData}
          >
            Export to Console
          </StyledButton>
        </View>

        <View style={{
          marginTop: 20,
          padding: 15,
          backgroundColor: theme.colors.backgroundSecondary,
          borderRadius: 10
        }}>
          <StyledText variant="caption" style={{ textAlign: 'center' }}>
            This dashboard is for development only.{'\n'}
            Remove before production deployment.
          </StyledText>
        </View>
      </View>
    </ScrollView>
  );
};

export default AnalyticsDashboard; 