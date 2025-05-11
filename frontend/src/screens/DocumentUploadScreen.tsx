import React, { useState } from 'react';
import { View, StyleSheet, Image, Alert, ScrollView } from 'react-native';
import { Appbar, Button, Text, RadioButton, TextInput, Snackbar, ProgressBar, Title, Surface, Card } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import { API_URL, MAX_FILE_SIZE, SUPPORTED_FILE_TYPES, DOCUMENT_TYPES } from '../config';

type DocumentUploadNavigationProp = NativeStackNavigationProp<RootStackParamList, 'DocumentUpload'>;

const DocumentUploadScreen = () => {
  const navigation = useNavigation<DocumentUploadNavigationProp>();
  
  const [selectedFile, setSelectedFile] = useState<DocumentPicker.DocumentPickerResult | null>(null);
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES.OTHER);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: SUPPORTED_FILE_TYPES,
        copyToCacheDirectory: true,
      });
      
      if (!result.canceled && result.assets && result.assets.length > 0) {
        const fileInfo = result.assets[0];
        // Check file size
        if (fileInfo.size && fileInfo.size > MAX_FILE_SIZE) {
          setError(`File is too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)} MB.`);
          setShowSnackbar(true);
          return;
        }
        
        setSelectedFile(result);
        setError('');
      }
    } catch (err) {
      console.error('Error picking document:', err);
      setError('Failed to select document. Please try again.');
      setShowSnackbar(true);
    }
  };

  const uploadDocument = async () => {
    if (!selectedFile || selectedFile.canceled || !selectedFile.assets || selectedFile.assets.length === 0) {
      setError('Please select a document first');
      setShowSnackbar(true);
      return;
    }

    const fileInfo = selectedFile.assets[0];
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      const token = await SecureStore.getItemAsync('authToken');
      
      if (!token) {
        throw new Error('Not authenticated');
      }
      
      // First, request a signed upload URL from the backend
      const { data: urlData } = await axios.post(
        `${API_URL}/api/v1/documents/upload_url`,
        {
          filename: fileInfo.name,
          content_type: fileInfo.mimeType,
          document_type: documentType,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      // Now upload the file directly to storage using the signed URL
      const fileUri = fileInfo.uri;
      const fileContent = await FileSystem.readAsStringAsync(fileUri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      
      // Convert base64 to blob
      const formData = new FormData();
      formData.append('file', {
        uri: fileUri,
        name: fileInfo.name,
        type: fileInfo.mimeType,
      } as any);
      
      // Upload using the signed URL
      await axios.put(urlData.upload_url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress / 100);
          }
        },
      });
      
      // Notify backend that upload is complete
      await axios.post(
        `${API_URL}/api/v1/documents/${urlData.document_id}/notify_upload`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      setSuccessMessage('Document uploaded successfully! Processing will begin shortly.');
      setShowSnackbar(true);
      
      // Reset form
      setSelectedFile(null);
      setDocumentType(DOCUMENT_TYPES.OTHER);
      
      // Navigate back to the home screen after a delay
      setTimeout(() => {
        navigation.goBack();
      }, 2000);
    } catch (err: any) {
      console.error('Error uploading document:', err);
      setError(err.message || 'Failed to upload document. Please try again.');
      setShowSnackbar(true);
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancel = () => {
    if (isUploading) {
      Alert.alert(
        'Cancel Upload',
        'Are you sure you want to cancel the upload?',
        [
          { text: 'No', style: 'cancel' },
          { 
            text: 'Yes', 
            onPress: () => {
              setIsUploading(false);
              setUploadProgress(0);
            } 
          }
        ]
      );
    } else {
      navigation.goBack();
    }
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={handleCancel} />
        <Appbar.Content title="Upload Document" />
      </Appbar.Header>
      
      <ScrollView contentContainerStyle={styles.content}>
        <Title style={styles.title}>Add Medical Document</Title>
        
        <Card style={styles.filePickerCard}>
          <Card.Content>
            <Button 
              mode="contained" 
              icon="file-upload" 
              onPress={pickDocument}
              disabled={isUploading}
              style={styles.uploadButton}
            >
              Select Document
            </Button>
            
            {selectedFile && !selectedFile.canceled && selectedFile.assets && selectedFile.assets.length > 0 && (
              <Surface style={styles.fileInfoContainer}>
                <Text style={styles.fileName}>
                  {selectedFile.assets[0].name}
                </Text>
                {selectedFile.assets[0].mimeType && (
                  <Text style={styles.fileType}>
                    Type: {selectedFile.assets[0].mimeType}
                  </Text>
                )}
                {selectedFile.assets[0].size && (
                  <Text style={styles.fileSize}>
                    Size: {(selectedFile.assets[0].size / 1024).toFixed(1)} KB
                  </Text>
                )}
              </Surface>
            )}
          </Card.Content>
        </Card>
        
        <Card style={styles.optionsCard}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Document Type</Text>
            
            <RadioButton.Group 
              onValueChange={value => setDocumentType(value)} 
              value={documentType}
            >
              <RadioButton.Item 
                label="Prescription" 
                value={DOCUMENT_TYPES.PRESCRIPTION} 
                disabled={isUploading}
              />
              <RadioButton.Item 
                label="Lab Result" 
                value={DOCUMENT_TYPES.LAB_RESULT} 
                disabled={isUploading}
              />
              <RadioButton.Item 
                label="Other Medical Document" 
                value={DOCUMENT_TYPES.OTHER} 
                disabled={isUploading}
              />
            </RadioButton.Group>
          </Card.Content>
        </Card>
        
        {isUploading && (
          <Card style={styles.progressCard}>
            <Card.Content>
              <Text style={styles.progressText}>
                Uploading... {Math.round(uploadProgress * 100)}%
              </Text>
              <ProgressBar progress={uploadProgress} color="#2A6BAC" style={styles.progressBar} />
            </Card.Content>
          </Card>
        )}
        
        <View style={styles.buttonContainer}>
          <Button 
            mode="outlined" 
            onPress={handleCancel} 
            style={styles.cancelButton}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button 
            mode="contained" 
            onPress={uploadDocument}
            loading={isUploading}
            disabled={isUploading || !selectedFile || selectedFile.canceled}
            style={styles.submitButton}
          >
            Upload Document
          </Button>
        </View>
      </ScrollView>
      
      <Snackbar
        visible={showSnackbar}
        onDismiss={() => setShowSnackbar(false)}
        duration={3000}
        action={{
          label: 'Dismiss',
          onPress: () => setShowSnackbar(false),
        }}
      >
        {error || successMessage}
      </Snackbar>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#2A6BAC',
    textAlign: 'center',
  },
  filePickerCard: {
    marginBottom: 16,
    elevation: 3,
  },
  uploadButton: {
    marginVertical: 16,
  },
  fileInfoContainer: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#E8F5E9',
    marginBottom: 8,
  },
  fileName: {
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 4,
  },
  fileType: {
    fontSize: 14,
    color: '#555',
  },
  fileSize: {
    fontSize: 14,
    color: '#555',
  },
  optionsCard: {
    marginBottom: 16,
    elevation: 3,
  },
  sectionTitle: {
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 8,
  },
  progressCard: {
    marginBottom: 16,
    elevation: 3,
  },
  progressText: {
    marginBottom: 8,
    textAlign: 'center',
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
    marginRight: 8,
  },
  submitButton: {
    flex: 2,
  },
});

export default DocumentUploadScreen; 