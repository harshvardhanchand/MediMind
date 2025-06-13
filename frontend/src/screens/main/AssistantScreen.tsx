import React, { useState, useRef, useEffect } from 'react';
import { View, FlatList, KeyboardAvoidingView, Platform, TouchableOpacity, TextInput, SafeAreaView } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import { MainAppStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme';
import StyledText from '../../components/common/StyledText';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledTextInput = styled(TextInput);
const StyledSafeAreaView = styled(SafeAreaView);

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

type AssistantScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Assistant'>;

const AssistantScreen = () => {
  const navigation = useNavigation<AssistantScreenNavigationProp>();
  const { colors } = useTheme();
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: '1', 
      text: "Hello! I'm your health assistant. I can help you understand your medical data, track symptoms, and answer health-related questions. How can I assist you today?", 
      sender: 'assistant',
      timestamp: new Date()
    },
  ]);
  const [inputText, setInputText] = useState('');
  const flatListRef = useRef<FlatList<Message>>(null);
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = () => {
    if (inputText.trim() === '') return;
    
    const newUserMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setInputText('');
    setIsTyping(true);
    
    // Scroll to bottom after sending message
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
    
    setTimeout(() => {
      setIsTyping(false);
      const assistantResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: getAssistantResponse(inputText),
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantResponse]);
    }, 1500);
  };

  const getAssistantResponse = (input: string) => {
    const lowercaseInput = input.toLowerCase();
    if (lowercaseInput.includes('blood pressure') || lowercaseInput.includes('bp')) {
      return "Your most recent blood pressure reading was 120/80 mmHg, taken yesterday at 9:00 AM. This is within the normal range. Would you like to see your blood pressure trends over the past month?";
    } else if (lowercaseInput.includes('medication') || lowercaseInput.includes('medicine')) {
      return "You have 3 medications scheduled for today: Lisinopril (10mg) at 9:00 AM, Metformin (500mg) at 7:00 PM, and your multivitamin. Would you like me to set a reminder?";
    } else if (lowercaseInput.includes('lab') || lowercaseInput.includes('test') || lowercaseInput.includes('results')) {
      return "Your most recent lab results from May 10 show normal blood glucose levels (98 mg/dL) and cholesterol within target range. Your doctor has left a note that everything looks good.";
    } else if (lowercaseInput.includes('appointment') || lowercaseInput.includes('doctor')) {
      return "Your next appointment is with Dr. Smith on June 15th at 10:30 AM. Would you like me to add this to your calendar or set a reminder?";
    } else {
      return `I understand you're asking about: "${input}". I'm still learning to respond to this type of query. For now, I can help with medications, lab results, vital readings, and appointment information. Is there something specific about your health data you'd like to know?`;
    }
  };

  useEffect(() => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.sender === 'user';
    
    return (
      <StyledView className={`mb-4 px-4 ${isUser ? 'items-end' : 'items-start'}`}>
        <StyledView className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-blue-500 rounded-br-md' 
            : 'bg-gray-100 rounded-bl-md'
        }`}>
          {!isUser && (
            <StyledView className="flex-row items-center mb-1">
              <Ionicons name="sparkles-outline" size={14} color={colors.accentPrimary} />
              <StyledText variant="caption" tw="ml-1 font-semibold text-blue-500">
                Health Assistant
              </StyledText>
            </StyledView>
          )}
          <StyledText 
            variant="body1" 
            style={{ 
              lineHeight: 20,
              color: isUser ? 'white' : colors.textPrimary
            }}
          >
            {item.text}
          </StyledText>
          <StyledText 
            variant="caption" 
            style={{
              color: isUser ? 'rgba(255,255,255,0.7)' : colors.textSecondary,
              marginTop: 4
            }}
            tw={isUser ? 'text-right' : 'text-left'}
          >
            {formatTime(item.timestamp)}
          </StyledText>
        </StyledView>
      </StyledView>
    );
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <StyledSafeAreaView className="flex-1 bg-white">
      {/* Header */}
      <StyledView className="flex-row items-center px-4 py-3 border-b border-gray-200 bg-white">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="mr-3">
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" tw="font-semibold">Health Assistant</StyledText>
      </StyledView>

      {/* Chat Area */}
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
        keyboardVerticalOffset={0}
      >
        <StyledView className="flex-1">
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={renderMessage}
            contentContainerStyle={{ 
              paddingTop: 16,
              paddingBottom: 20,
              flexGrow: 1
            }}
            showsVerticalScrollIndicator={false}
            style={{ flex: 1 }}
          />
          
          {/* Typing Indicator */}
          {isTyping && (
            <StyledView className="mb-4 px-4 items-start">
              <StyledView className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                <StyledView className="flex-row items-center">
                  <StyledView className="flex-row space-x-1">
                    <StyledView className="w-2 h-2 bg-gray-400 rounded-full" />
                    <StyledView className="w-2 h-2 bg-gray-400 rounded-full" />
                    <StyledView className="w-2 h-2 bg-gray-400 rounded-full" />
                  </StyledView>
                </StyledView>
              </StyledView>
            </StyledView>
          )}
        </StyledView>

        {/* Input Area - Fixed at bottom */}
        <StyledView 
          className="flex-row items-end px-4 py-3 bg-white border-t border-gray-200"
          style={{ 
            paddingBottom: Platform.OS === 'ios' ? 34 : 16 // Safe area for iPhone home indicator
          }}
        >
          <StyledView className="flex-1 flex-row items-end bg-gray-100 rounded-3xl px-4 py-2 mr-2">
            <StyledTextInput
              placeholder="Message..."
              value={inputText}
              onChangeText={setInputText}
              multiline
              style={{
                flex: 1,
                maxHeight: 100,
                fontSize: 16,
                lineHeight: 20,
                paddingTop: Platform.OS === 'ios' ? 8 : 4,
                paddingBottom: Platform.OS === 'ios' ? 8 : 4,
                color: colors.textPrimary
              }}
              placeholderTextColor={colors.textSecondary}
              onSubmitEditing={handleSendMessage}
              blurOnSubmit={false}
            />
          </StyledView>
          
          <StyledTouchableOpacity
            onPress={handleSendMessage}
            disabled={inputText.trim() === ''}
            className={`w-10 h-10 rounded-full items-center justify-center ${
              inputText.trim() === '' ? 'bg-gray-300' : 'bg-blue-500'
            }`}
          >
            <Ionicons 
              name="arrow-up" 
              size={20} 
              color="white"
            />
          </StyledTouchableOpacity>
        </StyledView>
      </KeyboardAvoidingView>
    </StyledSafeAreaView>
  );
};

export default AssistantScreen;