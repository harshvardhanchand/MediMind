import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/types';
import { Appbar, Card, Title, Paragraph, Divider, Chip, Button, ActivityIndicator, Text, List } from 'react-native-paper';
import { documentServices, extractedDataServices } from '../api/services';
import { DocumentRead, ExtractedDataResponse, ExtractionDetailsResponse, ProcessingStatus, ReviewStatus, DocumentType } from '../types/api';

type DocumentDetailRouteProp = RouteProp<RootStackParamList, 'DocumentDetail'>;
type DocumentDetailNavigationProp = NativeStackNavigationProp<RootStackParamList, 'DocumentDetail'>;

interface MedicalEvent {
  event_type?: string;
  description?: string;
  [key: string]: any;
}

const DocumentDetailScreen = () => {
  const route = useRoute<DocumentDetailRouteProp>();
  const navigation = useNavigation<DocumentDetailNavigationProp>();
  const { documentId } = route.params;
  
  const [details, setDetails] = useState<ExtractionDetailsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>('');
  const [expandedMedicalEvents, setExpandedMedicalEvents] = useState<string[]>([]);

  const fetchDocumentDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await extractedDataServices.getAllExtractedData(documentId);
      setDetails(response.data);
    } catch (err: any) {
      console.error('Error fetching document details:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load document details.');
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
            setLoading(true);
            try {
              await documentServices.deleteDocument(documentId);
              Alert.alert('Success', 'Document deleted successfully.');
              navigation.goBack();
            } catch (err: any) {
              console.error('Error deleting document:', err);
              Alert.alert('Error', err.response?.data?.detail || err.message || 'Failed to delete document.');
            } finally {
              setLoading(false);
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

  const getFormattedDate = (dateString?: string | null) => {
    if (!dateString) return 'Unknown date';
    try {
        return new Date(dateString).toLocaleDateString();
    } catch (e) {
        return dateString;
    }
  };

  const getStatusColor = (statusValue?: string | ProcessingStatus) => {
    const status = statusValue?.toString().toLowerCase();
    switch (status) {
      case ProcessingStatus.COMPLETED.toLowerCase(): return '#4CAF50';
      case ProcessingStatus.REVIEW_REQUIRED.toLowerCase(): return '#FFC107';
      case ProcessingStatus.OCR_COMPLETED?.toLowerCase():
      case ProcessingStatus.EXTRACTION_COMPLETED?.toLowerCase(): 
        return '#2196F3';
      case ProcessingStatus.PENDING.toLowerCase(): return '#9E9E9E';
      case ProcessingStatus.FAILED.toLowerCase(): return '#F44336';
      default: return '#9E9E9E';
    }
  };

  useEffect(() => {
    fetchDocumentDetails();
  }, [documentId]);

  const renderMedicalEvents = () => {
    const medicalEvents = details?.extracted_data?.content?.medical_events as MedicalEvent[] | undefined;
    if (!medicalEvents || medicalEvents.length === 0) {
      return (
        <Card style={styles.card}>
          <Card.Content>
            <Paragraph>No structured medical data extracted or available for review.</Paragraph>
          </Card.Content>
        </Card>
      );
    }

    return (
      <View style={styles.eventsContainer}>
        <Title style={styles.sectionTitle}>Extracted Medical Data</Title>
        {details?.extracted_data?.review_status && (
            <Chip 
                icon="information-outline" 
                style={{alignSelf: 'flex-start', marginBottom: 10, backgroundColor: '#E0E0E0'}} >
                Review Status: {details.extracted_data.review_status.replace('_',' ').toUpperCase()}
            </Chip>
        )}
        {medicalEvents.map((event, index) => {
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
              left={props => <List.Icon {...props} icon={isExpanded ? "chevron-up" : "chevron-down"} />}
            >
              {Object.entries(event).map(([key, value]) => {
                if (key === 'event_type' || key === 'description' || value === null || value === undefined || value === '') return null;
                return (
                  <List.Item
                    key={`${eventId}-${key}`}
                    title={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    description={typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                    descriptionNumberOfLines={10}
                    titleStyle={styles.listItemTitle}
                    descriptionStyle={styles.listItemDescription}
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
        <ActivityIndicator size="large" animating={true} />
        <Text style={styles.loadingText}>Loading document details...</Text>
      </View>
    );
  }

  if (error || !details) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error || 'Document data not found.'}</Text>
        <Button mode="contained" onPress={fetchDocumentDetails} style={styles.retryButton}>
          Retry
        </Button>
        <Button mode="outlined" onPress={() => navigation.goBack()} style={styles.backButton}>
          Go Back
        </Button>
      </View>
    );
  }

  const { document: docSummary, extracted_data } = details;

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Document Details" subtitle={docSummary.filename} subtitleStyle={{fontSize: 12}}/>
        <Appbar.Action icon="delete" onPress={handleDeleteDocument} />
      </Appbar.Header>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Card style={styles.card}>
          <Card.Content>
            <Chip 
              style={[styles.statusChip, { backgroundColor: getStatusColor(docSummary.processing_status) + '20' }]}
              textStyle={{ color: getStatusColor(docSummary.processing_status) }}
              icon="information-outline"
            >
              Processing: {docSummary.processing_status.replace('_', ' ').toUpperCase()}
            </Chip>
            
            <Divider style={styles.divider} />
            
            <View style={styles.metadataRow}>
              <Text style={styles.metadataLabel}>Type:</Text>
              <Text style={styles.metadataValue}>
                {docSummary.document_type.replace('_', ' ').toUpperCase()}
              </Text>
            </View>
            
            <View style={styles.metadataRow}>
              <Text style={styles.metadataLabel}>Uploaded:</Text>
              <Text style={styles.metadataValue}>
                {getFormattedDate(docSummary.upload_date)}
              </Text>
            </View>
            
            <Paragraph style={{ fontStyle: 'italic', fontSize: 12, marginTop: 10}}>
              Detailed metadata like specific document date, source, full tags, and file size may require fetching full document details if not included in this summary view.
            </Paragraph>
          </Card.Content>
        </Card>
        
        {extracted_data?.raw_text && (!extracted_data?.content?.medical_events || (extracted_data.content.medical_events as MedicalEvent[]).length === 0) && (
            <Card style={styles.card}>
                <Card.Content>
                    <Title style={styles.sectionTitle}>Raw Extracted Text</Title>
                    <Paragraph selectable>{extracted_data.raw_text}</Paragraph>
                </Card.Content>
            </Card>
        )}
        
        {renderMedicalEvents()}

        {extracted_data && (
             <Button 
                mode="contained-tonal" 
                icon="file-document-edit-outline"
                onPress={() => navigation.navigate('DataReview', { documentId: docSummary.document_id })}
                style={{marginTop: 16}}
            >
                Review & Correct Extracted Data
            </Button>
        )}
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
    borderRadius: 8,
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
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
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
    borderWidth: 1,
    borderColor: '#EEEEEE',
    borderRadius: 4,
  },
  listItemTitle: {
    textTransform: 'capitalize',
    fontWeight: '500',
  },
  listItemDescription: {
    fontSize: 13,
  }
});

export default DocumentDetailScreen; 