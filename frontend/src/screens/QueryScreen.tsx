import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Appbar, TextInput, Button, ActivityIndicator, Text, Chip, Card, Divider } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';

import { API_URL } from '../config';
import ErrorState from '../components/common/ErrorState';
import { crashReporting } from '../services/crashReporting';

// Example query suggestions
const QUERY_SUGGESTIONS = [
  "What were my glucose levels in the last 3 months?",
  "Show all medications prescribed by Dr. Smith",
  "When was my last cholesterol test?",
  "List all my lab tests from January",
  "What medicine was I prescribed for hypertension?",
];

const QueryScreen = () => {
  const navigation = useNavigation();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [criticalError, setCriticalError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);

  const handleQuerySubmit = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setShowSuggestions(false);

    try {
      crashReporting.addBreadcrumb('User submitted query', 'user-action', 'info');
      
      const token = await SecureStore.getItemAsync('auth_token');
      
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }
      
      const response = await axios.post(
        `${API_URL}/api/v1/query`,
        { query_text: query },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          timeout: 30000, // 30 second timeout
        }
      );
      
      setResult(response.data);
      crashReporting.addBreadcrumb('Query completed successfully', 'api-response', 'info');
      
    } catch (err: any) {
      console.error('Error processing query:', err);
      
      let errorMessage = 'Failed to process your query. Please try again.';
      
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        errorMessage = 'The request took too long to complete. Please try again.';
      } else if (err.response?.status === 401) {
        errorMessage = 'Your session has expired. Please log in again.';
      } else if (err.response?.status === 429) {
        errorMessage = 'Too many requests. Please wait a moment and try again.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message.includes('Authentication required')) {
        errorMessage = 'Your session has expired. Please log in again.';
      }
      
      setError(errorMessage);
      
      crashReporting.captureException(err, {
        context: 'query_submission',
        query: query,
        errorType: 'query_api_error',
        statusCode: err.response?.status,
      });
    } finally {
      setLoading(false);
    }
  };

  const selectSuggestion = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    setError(''); // Clear any previous errors
  };

  const retryOperation = () => {
    setCriticalError(null);
    setError('');
    setShowSuggestions(true);
  };

  const clearQuery = () => {
    setQuery('');
    setResult(null);
    setError('');
    setShowSuggestions(true);
  };

  const renderFilters = () => {
    if (!result?.query_interpretation?.filters || Object.keys(result.query_interpretation.filters).length === 0) {
      return null;
    }

    return (
      <Card style={styles.filtersCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Filters Applied</Text>
          <View style={styles.filtersContainer}>
            {Object.entries(result.query_interpretation.filters).map(([key, value]: [string, any], index: number) => {
              let displayValue: string;
              
              if (typeof value === 'object' && value !== null) {
                if ('start' in value && 'end' in value) {
                  displayValue = `${value.start} to ${value.end}`;
                } else {
                  displayValue = JSON.stringify(value);
                }
              } else {
                displayValue = String(value);
              }
              
              return (
                <Chip key={index} style={styles.filterChip}>
                  {key.replace(/_/g, ' ')}: {displayValue}
                </Chip>
              );
            })}
          </View>
        </Card.Content>
      </Card>
    );
  };

  const renderResults = () => {
    if (!result) return null;

    return (
      <View>
        {renderFilters()}
        
        <Card style={styles.resultCard}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Answer</Text>
            {result.has_results ? (
              <>
                <Text style={styles.answerText}>
                  {result.answer}
                </Text>
                
                {result.data && result.data.length > 0 && (
                  <>
                    <Divider style={styles.divider} />
                    
                    <Text style={styles.sectionTitle}>Data Points</Text>
                    {result.data.map((item: any, index: number) => (
                      <View key={index} style={styles.dataPointContainer}>
                        {Object.entries(item).map(([key, value]: [string, any]) => (
                          <View key={key} style={styles.dataPointRow}>
                            <Text style={styles.dataPointLabel}>
                              {key.replace(/_/g, ' ')}:
                            </Text>
                            <Text style={styles.dataPointValue}>
                              {String(value)}
                            </Text>
                          </View>
                        ))}
                        {index < result.data.length - 1 && (
                          <Divider style={styles.dataPointDivider} />
                        )}
                      </View>
                    ))}
                  </>
                )}
              </>
            ) : (
              <Text style={styles.noResultsText}>
                No data found matching your query. Try rephrasing or use different search terms.
              </Text>
            )}
          </Card.Content>
        </Card>
      </View>
    );
  };

  const renderSuggestions = () => {
    if (!showSuggestions) return null;

    return (
      <Card style={styles.suggestionsCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Try These Queries</Text>
          <View style={styles.suggestionsContainer}>
            {QUERY_SUGGESTIONS.map((suggestion, index) => (
              <TouchableOpacity key={index} onPress={() => selectSuggestion(suggestion)}>
                <Chip 
                  style={styles.suggestionChip}
                  icon="magnify"
                  onPress={() => selectSuggestion(suggestion)}
                >
                  {suggestion}
                </Chip>
              </TouchableOpacity>
            ))}
          </View>
        </Card.Content>
      </Card>
    );
  };

  // Show critical error state if needed
  if (criticalError) {
    return (
      <View style={styles.container}>
        <Appbar.Header>
          <Appbar.BackAction onPress={() => navigation.goBack()} />
          <Appbar.Content title="Query Your Data" />
        </Appbar.Header>
        <ErrorState
          title="Query Service Error"
          message={criticalError}
          onRetry={retryOperation}
          retryLabel="Try Again"
        />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 64 : 0}
    >
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Query Your Data" />
      </Appbar.Header>
      
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <Card style={styles.queryCard}>
          <Card.Content>
            <TextInput
              label="Ask a question about your medical data"
              value={query}
              onChangeText={setQuery}
              mode="outlined"
              multiline
              numberOfLines={3}
              style={styles.queryInput}
              right={
                query ? (
                  <TextInput.Icon 
                    icon="close" 
                    onPress={() => {
                      setQuery('');
                      setShowSuggestions(true);
                    }} 
                  />
                ) : undefined
              }
              onFocus={() => setShowSuggestions(true)}
            />
            
            {!!error && (
              <Text style={styles.errorText}>{error}</Text>
            )}
            
            <Button
              mode="contained"
              onPress={handleQuerySubmit}
              loading={loading}
              disabled={loading || !query.trim()}
              style={styles.queryButton}
            >
              Search
            </Button>
          </Card.Content>
        </Card>
        
        {renderSuggestions()}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" />
            <Text style={styles.loadingText}>Analyzing your data...</Text>
          </View>
        ) : (
          renderResults()
        )}
      </ScrollView>
    </KeyboardAvoidingView>
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
  queryCard: {
    marginBottom: 16,
    elevation: 3,
  },
  queryInput: {
    marginBottom: 8,
  },
  errorText: {
    color: 'red',
    marginBottom: 8,
  },
  queryButton: {
    marginTop: 8,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
  suggestionsCard: {
    marginBottom: 16,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 16,
    marginBottom: 12,
  },
  suggestionsContainer: {
    flexDirection: 'column',
    gap: 8,
  },
  suggestionChip: {
    marginBottom: 8,
  },
  filtersCard: {
    marginBottom: 16,
    elevation: 3,
  },
  filtersContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  filterChip: {
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#E3F2FD',
  },
  resultCard: {
    marginBottom: 16,
    elevation: 3,
  },
  answerText: {
    fontSize: 16,
    lineHeight: 24,
  },
  noResultsText: {
    fontStyle: 'italic',
    color: '#666',
  },
  divider: {
    marginVertical: 16,
  },
  dataPointContainer: {
    marginBottom: 8,
  },
  dataPointRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  dataPointLabel: {
    fontWeight: 'bold',
    width: 100,
    fontSize: 14,
  },
  dataPointValue: {
    flex: 1,
    fontSize: 14,
  },
  dataPointDivider: {
    marginVertical: 8,
  },
});

export default QueryScreen; 