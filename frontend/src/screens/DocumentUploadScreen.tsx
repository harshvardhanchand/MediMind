import React, { useState } from 'react';
import { View, StyleSheet, Alert, ScrollView } from 'react-native';
import {
  Appbar, Button, Text, RadioButton, Snackbar, 
  ProgressBar, Title, Card 
} from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/types';
import * as DocumentPicker from 'expo-document-picker';
import { MAX_FILE_SIZE, SUPPORTED_FILE_TYPES, DOCUMENT_TYPES } from '../config';
import { documentServices } from '../api/services';
import { DocumentType as DocumentTypeEnum } from '../types/api';

type DocumentUploadNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Upload'>;

const DocumentUploadScreen = () => {
  const navigation = useNavigation<DocumentUploadNavigationProp>();
  
  const [selectedFileAsset, setSelectedFileAsset] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [documentType, setDocumentType] = useState<string>(DOCUMENT_TYPES.OTHER);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const pickDocument = async () => {
    setError('');
    setSuccessMessage('');
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: SUPPORTED_FILE_TYPES,
        copyToCacheDirectory: true,
      });
      
      if (!result.canceled && result.assets && result.assets.length > 0) {
        const fileInfo = result.assets[0];
        if (fileInfo.size && fileInfo.size > MAX_FILE_SIZE) {
          setError(`File is too large. Max size is ${MAX_FILE_SIZE / (1024 * 1024)} MB.`);
          setShowSnackbar(true);
          setSelectedFileAsset(null);
          return;
        }
        setSelectedFileAsset(fileInfo);
      } else {
        setSelectedFileAsset(null);
      }
    } catch (err) {
      console.error('Error picking document:', err);
      setError('Failed to select document. Please try again.');
      setShowSnackbar(true);
      setSelectedFileAsset(null);
    }
  };

  const uploadDocument = async () => {
    if (!selectedFileAsset) {
      setError('Please select a document first');
      setShowSnackbar(true);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError('');
    setSuccessMessage('');
    
    const formData = new FormData();
    formData.append('file', {
      uri: selectedFileAsset.uri,
      name: selectedFileAsset.name,
      type: selectedFileAsset.mimeType,
    } as any);
    formData.append('document_type', documentType);

    try {
      const response = await documentServices.uploadDocument(formData);
      
      setSuccessMessage(`Document '${response.data.original_filename}' uploaded successfully! Processing...`);
      setShowSnackbar(true);
      setSelectedFileAsset(null);
      setDocumentType(DOCUMENT_TYPES.OTHER);
      
      setTimeout(() => {
        navigation.goBack();
      }, 2500);

    } catch (err: any) {
      console.error('Error uploading document:', err);
      let errorMessage = 'Failed to upload document. Please try again.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.detail.message) {
          errorMessage = `${err.response.data.detail.message}. Existing ID: ${err.response.data.detail.existing_document_id}`;
        }
      }
      setError(errorMessage);
      setShowSnackbar(true);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleCancel = () => {
    if (isUploading) {
        Alert.alert('Upload in Progress', 'Cannot cancel while upload is active with this method.');
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
            
            {selectedFileAsset && (
              <View style={styles.fileInfoContainer}>
                <Text style={styles.fileName}>
                  {selectedFileAsset.name}
                </Text>
                {selectedFileAsset.mimeType && (
                  <Text style={styles.fileType}>
                    Type: {selectedFileAsset.mimeType}
                  </Text>
                )}
                {selectedFileAsset.size && (
                  <Text style={styles.fileSize}>
                    Size: {(selectedFileAsset.size / 1024).toFixed(1)} KB
                  </Text>
                )}
              </View>
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
              <RadioButton.Item label="Prescription" value={DOCUMENT_TYPES.PRESCRIPTION} disabled={isUploading}/>
              <RadioButton.Item label="Lab Result" value={DOCUMENT_TYPES.LAB_RESULT} disabled={isUploading}/>
              <RadioButton.Item label="Other Medical Document" value={DOCUMENT_TYPES.OTHER} disabled={isUploading}/>
            </RadioButton.Group>
          </Card.Content>
        </Card>
        
        {isUploading && (
          <Card style={styles.progressCard}>
            <Card.Content>
              <Text style={styles.progressText}>
                Uploading document...
              </Text>
              <ProgressBar indeterminate={true} color="#2A6BAC" style={styles.progressBar} />
            </Card.Content>
          </Card>
        )}
        
        <View style={styles.buttonContainer}>
          <Button 
            mode="outlined" 
            onPress={handleCancel} 
            style={styles.cancelButton}
            disabled={isUploading && false}
          >
            Cancel / Back
          </Button>
          <Button 
            mode="contained" 
            onPress={uploadDocument}
            loading={isUploading}
            disabled={isUploading || !selectedFileAsset}
            style={styles.submitButton}
          >
            Upload Document
          </Button>
        </View>
      </ScrollView>
      
      <Snackbar
        visible={showSnackbar}
        onDismiss={() => setShowSnackbar(false)}
        duration={error ? 5000 : 3000}
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
    marginTop: 8,
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