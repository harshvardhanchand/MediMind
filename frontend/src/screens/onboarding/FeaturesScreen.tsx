import React, { useRef, useState } from 'react';
import { View, ScrollView, Dimensions, TouchableOpacity, Alert } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import { OnboardingStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import { useTheme } from '../../theme';
import { Feature } from '../../types/interfaces';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledScrollView = styled(ScrollView);

type FeaturesScreenNavigationProp = NativeStackNavigationProp<OnboardingStackParamList, 'Features'>;

const { width: screenWidth } = Dimensions.get('window');

const features: Feature[] = [
  {
    id: 1,
    icon: 'document-text',
    title: 'Smart Document Processing',
    description: 'Upload any medical document - prescriptions, lab results, reports. Our AI automatically extracts and organizes your health information.',
    color: '#667eea',
  },
  {
    id: 2,
    icon: 'bulb',
    title: 'AI Health Insights',
    description: 'Get intelligent medication alerts, health trend analysis, and personalized recommendations based on your medical history.',
    color: '#764ba2',
  },
  {
    id: 3,
    icon: 'shield-checkmark',
    title: 'Secure & Private',
    description: 'Bank-level encryption protects your health data. You control who sees what. Your medical information stays private, always.',
    color: '#10b981',
  },
];

const FeaturesScreen = () => {
  const navigation = useNavigation<FeaturesScreenNavigationProp>();
  const { colors } = useTheme();
  const [currentIndex, setCurrentIndex] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);

  const handleScroll = (event: any) => {
    const contentOffset = event.nativeEvent.contentOffset.x;
    const index = Math.round(contentOffset / screenWidth);
    setCurrentIndex(index);
  };

  const handleNext = () => {
    if (currentIndex < features.length - 1) {
      const nextIndex = currentIndex + 1;
      scrollViewRef.current?.scrollTo({ x: nextIndex * screenWidth, animated: true });
      setCurrentIndex(nextIndex);
    } else {
      // Show simple medical disclaimer for MVP
      Alert.alert(
        'Important Medical Disclaimer',
        'MediMind is NOT a medical device and does NOT provide medical advice. This app is for informational purposes only. Always consult healthcare professionals for medical decisions. Do not use for emergencies - call 911 instead.\n\nDo you accept these terms?',
        [
          {
            text: 'I Do Not Accept',
            style: 'cancel',
            onPress: () => {
              Alert.alert('Cannot Proceed', 'You must accept the medical disclaimer to use MediMind.');
            }
          },
          {
            text: 'I Accept',
            onPress: () => navigation.navigate('CreateProfile')
          }
        ]
      );
    }
  };

  const handleSkip = () => {
    // Show same disclaimer for skip
    Alert.alert(
      'Important Medical Disclaimer',
      'MediMind is NOT a medical device and does NOT provide medical advice. This app is for informational purposes only. Always consult healthcare professionals for medical decisions. Do not use for emergencies - call 911 instead.\n\nDo you accept these terms?',
      [
        {
          text: 'I Do Not Accept',
          style: 'cancel',
          onPress: () => {
            Alert.alert('Cannot Proceed', 'You must accept the medical disclaimer to use MediMind.');
          }
        },
        {
          text: 'I Accept',
          onPress: () => navigation.navigate('CreateProfile')
        }
      ]
    );
  };

  const renderFeature = (feature: Feature) => (
    <StyledView key={feature.id} style={{ width: screenWidth }} className="flex-1 justify-center items-center px-8">
      {/* Feature Icon */}
      <StyledView
        className="mb-8 rounded-full p-8 shadow-lg"
        style={{ backgroundColor: feature.color }}
      >
        <Ionicons name={feature.icon as any} size={80} color="white" />
      </StyledView>

      {/* Feature Title */}
      <StyledText
        variant="h1"
        tw="text-gray-900 text-3xl font-bold text-center mb-6"
      >
        {feature.title}
      </StyledText>

      {/* Feature Description */}
      <StyledText
        variant="body1"
        tw="text-gray-600 text-lg text-center leading-relaxed px-4"
      >
        {feature.description}
      </StyledText>
    </StyledView>
  );

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledView className="flex-1 bg-white">
        {/* Header */}
        <StyledView className="flex-row justify-between items-center px-6 pt-12 pb-4">
          <StyledTouchableOpacity onPress={handleSkip}>
            <StyledText tw="text-gray-500 font-medium">Skip</StyledText>
          </StyledTouchableOpacity>

          {/* Progress Dots */}
          <StyledView className="flex-row space-x-2">
            {features.map((_, index) => (
              <StyledView
                key={index}
                className={`w-2 h-2 rounded-full ${index === currentIndex ? 'bg-blue-500' : 'bg-gray-300'
                  }`}
              />
            ))}
          </StyledView>

          <StyledView style={{ width: 40 }} />
        </StyledView>

        {/* Features Carousel */}
        <StyledView className="flex-1">
          <StyledScrollView
            ref={scrollViewRef}
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            onScroll={handleScroll}
            scrollEventThrottle={16}
          >
            {features.map(renderFeature)}
          </StyledScrollView>
        </StyledView>

        {/* Bottom Navigation */}
        <StyledView className="px-8 pb-8">
          <StyledTouchableOpacity
            onPress={handleNext}
            className="bg-blue-500 rounded-full py-4 shadow-lg"
            style={{ elevation: 3 }}
          >
            <StyledView className="flex-row items-center justify-center">
              <StyledText tw="text-white font-bold text-lg mr-2">
                {currentIndex === features.length - 1 ? 'Continue' : 'Next'}
              </StyledText>
              <Ionicons name="arrow-forward" size={20} color="white" />
            </StyledView>
          </StyledTouchableOpacity>
        </StyledView>
      </StyledView>
    </ScreenContainer>
  );
};

export default FeaturesScreen; 