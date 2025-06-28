import React from 'react';
import ErrorBoundary from '../components/common/ErrorBoundary';

export function withScreenErrorBoundary<P extends object>(
    Component: React.ComponentType<P>,
    contextName: string
) {
    const WrappedComponent = (props: P) => (
        <ErrorBoundary
            level="screen"
            context={contextName}
            onError={(error, errorInfo) => {
                console.error(`🚨 ${contextName} Error Boundary triggered:`, error);
            }}
        >
            <Component {...props} />
        </ErrorBoundary>
    );


    WrappedComponent.displayName = `withErrorBoundary(${contextName})`;

    return WrappedComponent;
} 