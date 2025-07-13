import React, { useState, useEffect } from 'react';
import { View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { AuthStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import { styled } from 'nativewind';

const StyledView = styled(View);

type ConfirmNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Confirm'>;
type ConfirmRouteProp = RouteProp<AuthStackParamList, 'Confirm'>;

const ConfirmScreen = () => {
    const navigation = useNavigation<ConfirmNavigationProp>();
    const route = useRoute<ConfirmRouteProp>();
    const theme = useTheme();

    const { error_description } = route.params || {};

    const [redirectCountdown, setRedirectCountdown] = useState(3);

    useEffect(() => {
        // Only start countdown if there's no error
        if (!error_description) {
            const timer = setInterval(() => {
                setRedirectCountdown((prev) => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        navigation.navigate('Login');
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);

            return () => clearInterval(timer);
        }
    }, [navigation, error_description]);

    const handleManualRedirect = () => {
        navigation.navigate('Login');
    };

    return (
        <ScreenContainer withPadding>
            <StyledView className="flex-1 justify-center items-center">
                {error_description ? (
                    // Error State
                    <>
                        <StyledText variant="h1" className="text-center mb-4" style={{ fontSize: 48 }}>
                            ❌
                        </StyledText>
                        <StyledText variant="h2" className="text-center mb-2" color="error">
                            Confirmation Failed
                        </StyledText>
                        <StyledText variant="body1" className="text-center mb-6" color="textSecondary">
                            {error_description}
                        </StyledText>
                        <StyledButton
                            variant="filledPrimary"
                            onPress={handleManualRedirect}
                            className="w-full"
                        >
                            Go to Login
                        </StyledButton>
                    </>
                ) : (
                    // Success State
                    <>
                        <StyledText variant="h1" className="text-center mb-4" style={{ fontSize: 48 }}>
                            ✅
                        </StyledText>
                        <StyledText variant="h2" className="text-center mb-2" color="primary">
                            Email Confirmed!
                        </StyledText>
                        <StyledText variant="body1" className="text-center mb-6" color="textSecondary">
                            Your email has been successfully confirmed. You can now log in to your account.
                        </StyledText>
                        <StyledText variant="body2" className="text-center mb-4" color="textMuted">
                            Redirecting to login in {redirectCountdown}s...
                        </StyledText>
                        <StyledButton
                            variant="filledPrimary"
                            onPress={handleManualRedirect}
                            className="w-full"
                        >
                            Go to Login
                        </StyledButton>
                    </>
                )}
            </StyledView>
        </ScreenContainer>
    );
};

export default ConfirmScreen;
