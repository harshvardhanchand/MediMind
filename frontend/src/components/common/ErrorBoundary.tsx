import React, { Component, ReactNode } from 'react';
import { View, Alert } from 'react-native';
import { useTheme } from '../../theme';
import StyledText from './StyledText';
import StyledButton from './StyledButton';
import { analytics } from '../../services/analytics';
import { crashReporting } from '../../services/crashReporting';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  level?: 'global' | 'screen' | 'component';
  context?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorId: string | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Track error in analytics
    analytics.track('error_boundary_triggered', {
      error_message: error.message,
      error_stack: error.stack,
      component_stack: errorInfo.componentStack,
      level: this.props.level || 'unknown',
      context: this.props.context || 'unknown',
      error_id: this.state.errorId,
    });

    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Send to crash reporting service (Sentry)
    crashReporting.captureException(error, {
      componentStack: errorInfo.componentStack,
      level: this.props.level,
      context: this.props.context,
      errorId: this.state.errorId,
    });
  }

  handleRetry = () => {
    // Track retry attempt
    analytics.track('error_boundary_retry', {
      error_id: this.state.errorId,
      level: this.props.level,
      context: this.props.context,
    });

    // Reset error state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  handleReportError = () => {
    const { error, errorInfo, errorId } = this.state;
    
    // Create error report
    const errorReport = {
      errorId,
      message: error?.message,
      stack: error?.stack,
      componentStack: errorInfo?.componentStack,
      level: this.props.level,
      context: this.props.context,
      timestamp: new Date().toISOString(),
    };

    // Track error report
    analytics.track('error_boundary_reported', {
      error_id: errorId,
      level: this.props.level,
    });

    // Show confirmation to user
    Alert.alert(
      'Error Reported',
      'Thank you for reporting this error. Our team will investigate and fix it.',
      [{ text: 'OK' }]
    );

    console.log('Error Report:', errorReport);
    // TODO: Send to error reporting service
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI based on error level
      return <ErrorFallbackUI 
        level={this.props.level || 'component'}
        context={this.props.context}
        error={this.state.error}
        onRetry={this.handleRetry}
        onReport={this.handleReportError}
      />;
    }

    return this.props.children;
  }
}

// Fallback UI component
const ErrorFallbackUI: React.FC<{
  level: string;
  context?: string;
  error: Error | null;
  onRetry: () => void;
  onReport: () => void;
}> = ({ level, context, error, onRetry, onReport }) => {
  const theme = useTheme();

  const getErrorTitle = () => {
    switch (level) {
      case 'global':
        return 'App Error';
      case 'screen':
        return 'Screen Error';
      case 'component':
        return 'Component Error';
      default:
        return 'Something went wrong';
    }
  };

  const getErrorMessage = () => {
    switch (level) {
      case 'global':
        return 'The app encountered an unexpected error. Please restart the app.';
      case 'screen':
        return 'This screen encountered an error. Please try again or go back.';
      case 'component':
        return 'A component failed to load. Please try refreshing this section.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  };

  return (
    <View style={{
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
      backgroundColor: theme.colors.backgroundPrimary,
    }}>
      <StyledText 
        variant="h2" 
        style={{ 
          color: theme.colors.error, 
          marginBottom: 16,
          textAlign: 'center',
        }}
      >
        {getErrorTitle()}
      </StyledText>
      
      <StyledText 
        variant="body1" 
        style={{ 
          color: theme.colors.textSecondary,
          marginBottom: 24,
          textAlign: 'center',
          lineHeight: 24,
        }}
      >
        {getErrorMessage()}
      </StyledText>

      {context && (
        <StyledText 
          variant="caption" 
          style={{ 
            color: theme.colors.textMuted,
            marginBottom: 24,
            textAlign: 'center',
          }}
        >
          Context: {context}
        </StyledText>
      )}

      <View style={{ gap: 12, width: '100%', maxWidth: 300 }}>
        <StyledButton
          variant="filledPrimary"
          onPress={onRetry}
        >
          Try Again
        </StyledButton>
        
        <StyledButton
          variant="textPrimary"
          onPress={onReport}
        >
          Report Error
        </StyledButton>
      </View>

      {__DEV__ && error && (
        <View style={{ 
          marginTop: 24, 
          padding: 12, 
          backgroundColor: theme.colors.backgroundSecondary,
          borderRadius: 8,
          maxWidth: '100%',
        }}>
          <StyledText 
            variant="caption" 
            style={{ 
              color: theme.colors.textMuted,
              fontFamily: 'monospace',
            }}
          >
            {error.message}
          </StyledText>
        </View>
      )}
    </View>
  );
};

export default ErrorBoundary; 