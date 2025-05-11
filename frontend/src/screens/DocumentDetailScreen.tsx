import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { Appbar, Card, Title, Paragraph, Divider, Chip, Button, ActivityIndicator, Text, List } from 'react-native-paper';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import { API_URL } from '../config';

type DocumentDetailRouteProp = RouteProp<RootStackParamList, 'DocumentDetail'>;
type DocumentDetailNavigationProp = NativeStackNavigationProp<RootStackParamList, 'DocumentDetail'>;

interface Document {
  document_id: string;
  original_filename: string;
  document_type: string;
  upload_timestamp: string;
  processing_status: string;
  document_date?: string;
  source_name?: string;
  source_location_city?: string;
  tags?: string[];
  file_metadata?: {
    content_type: string;
    size: number;
  };
}

interface ExtractedData {
  extracted_data_id: string;
  document_id: string;
  content: any; // JSON content
  raw_text?: string;
  extraction_timestamp: string;
  review_status: string;
}

interface DocumentWithExtractedData {
  document: Document;
  extracted_data?: ExtractedData;
}

const DocumentDetailScreen = () => {
  const route = useRoute<DocumentDetailRouteProp>();
  const navigation = useNavigation<DocumentDetailNavigationProp>();
  const { documentId } = route.params;
  
  const [data, setData] = useState<DocumentWithExtractedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedMedicalEvents, setExpandedMedicalEvents] = useState<string[]>([]);

  const fetchDocumentDetails = async () => {
    try {
      const token = await SecureStore.getItemAsync('authToken');
      
      if (!token) {
        throw new Error('Not authenticated');
      }
      
      // Fetch combined document and extracted data
      const response = await axios.get(`${API_URL}/api/v1/extracted_data/all/${documentId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      setData(response.data);
      setError('');
    } catch (err: any) {
      console.error('Error fetching document details:', err);
      setError('Failed to load document details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async () => {
    Alert.alert(
      'Delete Document',
      'Are you sure you want to delete this document? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              const token = await SecureStore.getItemAsync('authToken');
              
              if (!token) {
                throw new Error('Not authenticated');
              }
              
              await axios.delete(`${API_URL}/api/v1/documents/${documentId}`, {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              });
              
              // Go back to the home screen
              navigation.goBack();
            } catch (err: any) {
              console.error('Error deleting document:', err);
              Alert.alert('Error', 'Failed to delete document. Please try again.');
            }
          }
        },
      ]
    );
  };

  const toggleMedicalEvent = (eventId: string) => {
    setExpandedMedicalEvents(prev => 
      prev.includes(eventId) 
        ? prev.filter(id => id !== eventId) 
        : [...prev, eventId]
    );
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const getFormattedDate = (dateString?: string) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString();
  };

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

  useEffect(() => {
    fetchDocumentDetails();
  }, [documentId]);

  const renderMedicalEvents = () => {
    if (!data?.extracted_data?.content?.medical_events) {
      return (
        <Card style={styles.card}>
          <Card.Content>
            <Paragraph>No medical data has been extracted from this document yet.</Paragraph>
          </Card.Content>
        </Card>
      );
    }

    return (
      <View style={styles.eventsContainer}>
        <Title style={styles.sectionTitle}>Extracted Medical Data</Title>
        {data.extracted_data.content.medical_events.map((event: any, index: number) => {
          const eventId = `event-${index}`;
          const isExpanded = expandedMedicalEvents.includes(eventId);
          
          return (
            <List.Accordion
              key={eventId}
              title={event.event_type || 'Medical Event'}
              description={event.description || `Entry ${index + 1}`}
              expanded={isExpanded}
              onPress={() => toggleMedicalEvent(eventId)}
              style={styles.accordionItem}
            >
              {Object.entries(event).map(([key, value]) => {
                if (key === 'event_type' || key === 'description' || !value) return null;
                return (
                  <List.Item
                    key={`${eventId}-${key}`}
                    title={key.replace(/_/g, ' ')}
                    description={String(value)}
                    descriptionNumberOfLines={3}
                    titleStyle={styles.listItemTitle}
                  />
                );
              })}
            </List.Accordion>
          );
        })}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading document details...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error || 'Document not found'}</Text>
        <Button mode="contained" onPress={fetchDocumentDetails} style={styles.retryButton}>
          Retry
        </Button>
        <Button mode="outlined" onPress={() => navigation.goBack()} style={styles.backButton}>
          Go Back
        </Button>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Document Details" />
        <Appbar.Action icon="delete" onPress={handleDeleteDocument} />
      </Appbar.Header>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>{data.document.original_filename}</Title>
            
            <Chip 
              style={[styles.statusChip, { backgroundColor: getStatusColor(data.document.processing_status) + '20' }]}
              textStyle={{ color: getStatusColor(data.document.processing_status) }}
            >
              {data.document.processing_status.replace('_', ' ')}
            </Chip>
            
            <Divider style={styles.divider} />
            
            <View style={styles.metadataRow}>
              <Text style={styles.metadataLabel}>Document Type:</Text>
              <Text style={styles.metadataValue}>
                {data.document.document_type.replace('_', ' ')}
              </Text>
            </View>
            
            <View style={styles.metadataRow}>
              <Text style={styles.metadataLabel}>Upload Date:</Text>
              <Text style={styles.metadataValue}>
                {getFormattedDate(data.document.upload_timestamp)}
              </Text>
            </View>
            
            {data.document.document_date && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Document Date:</Text>
                <Text style={styles.metadataValue}>
                  {getFormattedDate(data.document.document_date)}
                </Text>
              </View>
            )}
            
            {data.document.source_name && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Source:</Text>
                <Text style={styles.metadataValue}>{data.document.source_name}</Text>
              </View>
            )}
            
            {data.document.source_location_city && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Location:</Text>
                <Text style={styles.metadataValue}>{data.document.source_location_city}</Text>
              </View>
            )}
            
            {data.document.file_metadata && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>File Size:</Text>
                <Text style={styles.metadataValue}>
                  {formatFileSize(data.document.file_metadata.size)}
                </Text>
              </View>
            )}
          </Card.Content>
        </Card>
        
        {data.document.tags && data.document.tags.length > 0 && (
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.sectionTitle}>Tags</Title>
              <View style={styles.tagsContainer}>
                {data.document.tags.map((tag, index) => (
                  <Chip key={index} style={styles.tag}>
                    {tag}
                  </Chip>
                ))}
              </View>
            </Card.Content>
          </Card>
        )}
        
        {renderMedicalEvents()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  card: {
    marginBottom: 16,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  divider: {
    marginVertical: 12,
  },
  statusChip: {
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  metadataRow: {
    flexDirection: 'row',
    marginVertical: 4,
  },
  metadataLabel: {
    width: 100,
    fontWeight: 'bold',
    fontSize: 14,
  },
  metadataValue: {
    flex: 1,
    fontSize: 14,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#E1F5FE',
  },
  sectionTitle: {
    fontSize: 16,
    marginBottom: 12,
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
    marginBottom: 16,
  },
  backButton: {
    marginTop: 8,
  },
  eventsContainer: {
    marginBottom: 16,
  },
  accordionItem: {
    marginBottom: 2,
    backgroundColor: 'white',
  },
  listItemTitle: {
    textTransform: 'capitalize',
  },
});

export default DocumentDetailScreen; 