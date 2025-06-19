import React, { useState } from 'react';
import { View, StyleSheet, Alert, ScrollView } from 'react-native';
import {
  Appbar, Button, Text, RadioButton, Snackbar, 
  ProgressBar, Card 
} from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as DocumentPicker from 'expo-document-picker';

import { RootStackParamList } from '../navigation/types';
import { MAX_FILE_SIZE, SUPPORTED_FILE_TYPES, DOCUMENT_TYPES } from '../config';
import { documentServices } from '../api/services';
import ErrorState from '../components/common/ErrorState';
import { ERROR_MESSAGES, SUCCESS_MESSAGES, LOADING_MESSAGES } from '../constants/messages';

type DocumentUploadNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Upload'>;

const DocumentUploadScreen = () => {
  const navigation = useNavigation<DocumentUploadNavigationProp>();
  
  const [selectedFileAssets, setSelectedFileAssets] = useState<DocumentPicker.DocumentPickerAsset[]>([]);
  const [documentType, setDocumentType] = useState<string>(DOCUMENT_TYPES.PRESCRIPTION);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [criticalError, setCriticalError] = useState<string | null>(null);

  const pickDocument = async () => {
    setError('');
    setSuccessMessage('');
    setCriticalError(null);
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: SUPPORTED_FILE_TYPES,
        copyToCacheDirectory: true,
        multiple: true,
      });
      
      if (!result.canceled && result.assets && result.assets.length > 0) {
        if (result.assets.length > 5) {
          setError('Maximum 5 files allowed per upload. Please select fewer files.');
          setShowSnackbar(true);
          return;
        }
        
        const invalidFiles = result.assets.filter(file => 
          file.size && file.size > MAX_FILE_SIZE
        );
        
        if (invalidFiles.length > 0) {
          setError(ERROR_MESSAGES.FILE_TOO_LARGE);
          setShowSnackbar(true);
          return;
        }
        
        setSelectedFileAssets(result.assets);
      } else {
        setSelectedFileAssets([]);
      }
    } catch (err) {
      console.error('Error picking documents:', err);
      setError(ERROR_MESSAGES.GENERIC_ERROR);
      setShowSnackbar(true);
      setSelectedFileAssets([]);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = [...selectedFileAssets];
    newFiles.splice(index, 1);
    setSelectedFileAssets(newFiles);
  };

  const uploadDocument = async () => {
    if (!selectedFileAssets || selectedFileAssets.length === 0) {
      setError('Please select at least one document first');
      setShowSnackbar(true);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError('');
    setSuccessMessage('');
    setCriticalError(null);
    
    const formData = new FormData();
    
    selectedFileAssets.forEach((fileAsset) => {
      formData.append('files', {
        uri: fileAsset.uri,
        name: fileAsset.name,
        type: fileAsset.mimeType,
      } as any);
    });
    
    formData.append('document_type', documentType);

    try {
      const response = await documentServices.uploadDocument(formData);
      
      // Handle response which is now an array of uploaded documents
      const uploadedDocuments = Array.isArray(response.data) ? response.data : [response.data];
      const uploadedCount = uploadedDocuments.length;
      const totalCount = selectedFileAssets.length;
      
      if (uploadedCount === totalCount) {
        setSuccessMessage(SUCCESS_MESSAGES.DOCUMENT_UPLOADED);
      } else {
        setSuccessMessage(`${uploadedCount} of ${totalCount} documents uploaded successfully! Check logs for failed uploads.`);
      }
      
      setShowSnackbar(true);
      setSelectedFileAssets([]);
      setDocumentType(DOCUMENT_TYPES.PRESCRIPTION);
      
      setTimeout(() => {
        navigation.goBack();
      }, 2500);

    } catch (err: any) {
      console.error('Error uploading documents:', err);
      let errorMessage = ERROR_MESSAGES.UPLOAD_ERROR;
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.detail.message) {
          errorMessage = err.response.data.detail.message;
          if (err.response.data.detail.failed_uploads) {
            const failedNames = err.response.data.detail.failed_uploads.map((f: any) => f.filename).join(', ');
            errorMessage += ` Failed files: ${failedNames}`;
          }
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

  const retryOperation = () => {
    setCriticalError(null);
    setError('');
    setSuccessMessage('');
    // Reset form to initial state if needed
  };

  // ✅ Render critical error state using standardized ErrorState component
  if (criticalError) {
    return (
      <View style={styles.container}>
        <Appbar.Header>
          <Appbar.BackAction onPress={() => navigation.goBack()} />
          <Appbar.Content title="Upload Document" />
        </Appbar.Header>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 16 }}>
          <ErrorState
            title="Unable to Load Upload Form"
            message={criticalError}
            onRetry={retryOperation}
            retryLabel="Try Again"
            icon="cloud-upload-outline"
          />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={handleCancel} />
        <Appbar.Content title="Upload Document" />
      </Appbar.Header>
      
      <ScrollView contentContainerStyle={styles.content}>
        <Text variant="headlineSmall" style={styles.title}>Add Medical Document</Text>
        
        <Card style={styles.filePickerCard}>
          <Card.Content>
            <Button 
              mode="contained" 
              icon="file-upload" 
              onPress={pickDocument}
              disabled={isUploading}
              style={styles.uploadButton}
            >
              Select Documents
            </Button>
            
            {selectedFileAssets.map((fileAsset, index) => (
              <View key={index} style={styles.fileInfoContainer}>
                <Text style={styles.fileName}>
                  {fileAsset.name}
                </Text>
                {fileAsset.mimeType && (
                  <Text style={styles.fileType}>
                    Type: {fileAsset.mimeType}
                  </Text>
                )}
                {fileAsset.size && (
                  <Text style={styles.fileSize}>
                    Size: {(fileAsset.size / 1024).toFixed(1)} KB
                  </Text>
                )}
                <Button 
                  mode="outlined" 
                  onPress={() => removeFile(index)}
                  style={styles.removeButton}
                >
                  Remove
                </Button>
              </View>
            ))}
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
              <RadioButton.Item label="Imaging Report" value={DOCUMENT_TYPES.IMAGING_REPORT} disabled={isUploading}/>
              <RadioButton.Item label="Discharge Summary" value={DOCUMENT_TYPES.DISCHARGE_SUMMARY} disabled={isUploading}/>
            </RadioButton.Group>
          </Card.Content>
        </Card>
        
        {isUploading && (
          <Card style={styles.progressCard}>
            <Card.Content>
              <Text style={styles.progressText}>
                {LOADING_MESSAGES.UPLOADING_DOCUMENT}
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
            Cancel
          </Button>
          <Button 
            mode="contained" 
            onPress={uploadDocument}
            loading={isUploading}
            disabled={isUploading || !selectedFileAssets || selectedFileAssets.length === 0}
            style={styles.submitButton}
          >
            Upload Documents
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
  removeButton: {
    marginTop: 8,
  },
});

export default DocumentUploadScreen; 