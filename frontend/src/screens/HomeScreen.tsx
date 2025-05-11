import React, { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, ScrollView } from 'react-native';
import { Appbar, FAB, Card, Title, Paragraph, Divider, Chip, Button, ActivityIndicator, Text, IconButton } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
// import * as SecureStore from 'expo-secure-store'; // Commented out for mock data
// import axios from 'axios'; // Commented out for mock data
import { supabaseClient } from '../services/supabase'; // Keep for logout
// import { API_URL } from '../config'; // Commented out for mock data

// Import mock data
import { mockDocuments, MockDocument } from '../data/mockData';


type HomeScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Home'>;

// Document type definition based on API response (using MockDocument now)
interface Document extends MockDocument {}

const HomeScreen = () => {
  const navigation = useNavigation<HomeScreenNavigationProp>();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true); // Set to false initially for mock data
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const fetchDocuments = async () => {
    // setLoading(true); // Already handled by useEffect or initial state for mock data
    // try {
    //   const token = await SecureStore.getItemAsync(\'authToken\');
      
    //   if (!token) {
    //     throw new Error(\'Not authenticated\');
    //   }
      
    //   const response = await axios.get(`${API_URL}/api/v1/documents`, {
    //     headers: {
    //       Authorization: `Bearer ${token}`,
    //     },
    //   });
      
    //   setDocuments(response.data.items || []);
    //   setError(\'\');
    // } catch (err: any) {
    //   console.error(\'Error fetching documents:\', err);
    //   setError(\'Failed to load documents. Please try again.\');
    // } finally {
    //   setLoading(false);
    //   setRefreshing(false);
    // }

    // Simulate API call for mock data
    console.log('Using mock documents for HomeScreen');
    setDocuments(mockDocuments);
    setLoading(false);
    setRefreshing(false);
    setError('');
  };

  const handleLogout = async () => {
    try {
      await supabaseClient.auth.signOut();
      // await SecureStore.deleteItemAsync(\'authToken\'); // Handled by AppNavigator logic too
      // await SecureStore.deleteItemAsync(\'refreshToken\');
      
      // AppNavigator will detect the authentication state change
      // and redirect to Login screen based on its own SecureStore check.
      // Forcing navigation reset here ensures a clean state if AppNavigator\'s effect is delayed.
      navigation.reset({
        index: 0,
        routes: [{ name: 'Login' }],
      });
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchDocuments();
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  // Feature menu cards for navigation
  const renderFeatureCards = () => {
    return (
      <ScrollView contentContainerStyle={styles.featureCardsContainer}>
        <Title style={styles.sectionTitle}>Medical Data Hub</Title>
        <Paragraph style={styles.sectionSubtitle}>
          Manage your health data in one secure place
        </Paragraph>

        <View style={styles.cardsRow}>
          {/* Documents Card */}
          <Card style={styles.featureCard} onPress={() => onRefresh()}>
            <Card.Content>
              <IconButton icon="file-document" size={32} style={styles.featureIcon} />
              <Title style={styles.featureTitle}>Documents</Title>
              <Paragraph>View and manage your medical documents</Paragraph>
            </Card.Content>
          </Card>

          {/* Medications Card */}
          <Card style={styles.featureCard} onPress={() => navigation.navigate('Medications')}>
            <Card.Content>
              <IconButton icon="pill" size={32} style={styles.featureIcon} />
              <Title style={styles.featureTitle}>Medications</Title>
              <Paragraph>Track your medications and schedule</Paragraph>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.cardsRow}>
          {/* Health Readings Card */}
          <Card style={styles.featureCard} onPress={() => navigation.navigate('HealthReadings')}>
            <Card.Content>
              <IconButton icon="heart-pulse" size={32} style={styles.featureIcon} />
              <Title style={styles.featureTitle}>Health Readings</Title>
              <Paragraph>Monitor your health metrics</Paragraph>
            </Card.Content>
          </Card>

          {/* Query Assistant Card */}
          <Card style={styles.featureCard} onPress={() => navigation.navigate('Query')}>
            <Card.Content>
              <IconButton icon="chat-question" size={32} style={styles.featureIcon} />
              <Title style={styles.featureTitle}>AI Assistant</Title>
              <Paragraph>Ask questions about your health data</Paragraph>
            </Card.Content>
          </Card>
        </View>
      </ScrollView>
    );
  };

  const renderDocumentCard = ({ item }: { item: Document }) => {
    const getStatusColor = (status: string) => {
      switch (status) {
        case 'completed': return '#4CAF50';
        case 'review_required': return '#FFC107';
        case 'processing': return '#2196F3';
        case 'pending': return '#9E9E9E';
        case 'failed': return '#F44336';
        default: return '#9E9E9E';
      }
    };

    const formattedDate = item.upload_timestamp 
      ? new Date(item.upload_timestamp).toLocaleDateString() 
      : 'Unknown date';

    return (
      <Card style={styles.card} onPress={() => navigation.navigate('DocumentDetail', { documentId: item.document_id })}>
        <Card.Content>
          <Title style={styles.cardTitle}>{item.original_filename}</Title>
          
          <View style={styles.cardMetaRow}>
            <Paragraph>Uploaded: {formattedDate}</Paragraph>
            <Chip 
              style={[styles.statusChip, { backgroundColor: getStatusColor(item.processing_status) + '20' }]}
              textStyle={{ color: getStatusColor(item.processing_status) }}
            >
              {item.processing_status.replace('_', ' ')}
            </Chip>
          </View>
          
          {item.document_type && (
            <Chip style={styles.typeChip}>
              {item.document_type.replace('_', ' ')}
            </Chip>
          )}
          
          {item.source_name && (
            <Paragraph style={styles.sourceText}>
              Source: {item.source_name}
            </Paragraph>
          )}
          
          {item.tags && item.tags.length > 0 && (
            <View style={styles.tagsContainer}>
              {item.tags.slice(0, 3).map((tag, index) => (
                <Chip key={index} style={styles.tag}>
                  {tag}
                </Chip>
              ))}
              {item.tags.length > 3 && (
                <Chip>+{item.tags.length - 3}</Chip>
              )}
            </View>
          )}
        </Card.Content>
      </Card>
    );
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.Content title="Medical Data Hub" />
        <Appbar.Action icon="magnify" onPress={() => navigation.navigate('Query')} />
        <Appbar.Action icon="logout" onPress={handleLogout} />
      </Appbar.Header>
      
      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Loading your dashboard...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <Button mode="contained" onPress={fetchDocuments} style={styles.retryButton}>
            Retry
          </Button>
        </View>
      ) : (
        <>
          {documents.length === 0 ? (
            renderFeatureCards()
          ) : (
            <>
              {renderFeatureCards()}
              <Divider style={styles.divider} />
              <Title style={styles.recentTitle}>Recent Documents</Title>
              <FlatList
                data={documents.slice(0, 3)} // Show only the 3 most recent documents
                renderItem={renderDocumentCard}
                keyExtractor={(item) => item.document_id}
                contentContainerStyle={styles.listContainer}
                refreshControl={
                  <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
              />
            </>
          )}
        </>
      )}
      
      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate('DocumentUpload')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  listContainer: {
    padding: 16,
    paddingTop: 0,
  },
  card: {
    marginBottom: 16,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  cardMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusChip: {
    height: 28,
  },
  typeChip: {
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  tag: {
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#E1F5FE',
  },
  sourceText: {
    fontStyle: 'italic',
    fontSize: 14,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: 'red',
    marginBottom: 16,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 18,
    marginBottom: 8,
  },
  emptySubText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  featureCardsContainer: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2A6BAC',
    textAlign: 'center',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  cardsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  featureCard: {
    flex: 1,
    marginHorizontal: 8,
    elevation: 3,
  },
  featureIcon: {
    alignSelf: 'center',
    margin: 8,
    backgroundColor: '#E1F5FE',
  },
  featureTitle: {
    fontSize: 18,
    textAlign: 'center',
  },
  divider: {
    marginVertical: 16,
  },
  recentTitle: {
    fontSize: 20,
    marginLeft: 16,
    marginBottom: 8,
  },
});

export default HomeScreen; 