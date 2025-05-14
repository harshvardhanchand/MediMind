import React, { useState, useRef, useEffect } from 'react';
import { View, FlatList, KeyboardAvoidingView, Platform, TouchableOpacity, TextInput } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import Ionicons from 'react-native-vector-icons/Ionicons';
import { useTheme } from '../../theme';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledInput from '../../components/common/StyledInput';
import StyledButton from '../../components/common/StyledButton';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

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
    
    // Base bubble style
    let bubbleTw = 'my-1.5 mx-3 max-w-[80%] rounded-2xl p-3 shadow-sm'; // Added slightly more horizontal margin and subtle shadow
    let specificCornerTw = '';

    if (isUser) {
      bubbleTw += ' bg-accentPrimary self-end';
      specificCornerTw = 'rounded-br-lg'; // Sharper bottom-right corner for user
    } else {
      bubbleTw += ' bg-backgroundSecondary self-start'; // Changed assistant to white for better contrast, similar to iMessage
      specificCornerTw = 'rounded-bl-lg'; // Sharper bottom-left corner for assistant
    }

    return (
      <StyledView tw={`${bubbleTw} ${specificCornerTw}`.trim()}>
        {!isUser && (
          <StyledView tw="flex-row items-center mb-1">
            <Ionicons name="sparkles-outline" size={16} color={colors.accentPrimary} />
            <StyledText variant="label" tw="ml-1.5 font-semibold" color="accentPrimary">
              Health Assistant
            </StyledText>
          </StyledView>
        )}
        <StyledText 
          variant="body1" 
          style={{ lineHeight: 21 }} // Slightly increased line height
          color={isUser ? 'textOnPrimaryColor' : 'textPrimary'}
        >
          {item.text}
        </StyledText>
        <StyledText 
          variant="caption" 
          // For assistant, use textMuted. For user, slightly lighter than main bubble text.
          style={{color: isUser ? colors.textOnPrimaryColor : colors.textMuted, opacity: isUser ? 0.75 : 1}}
          tw={`mt-1.5 text-xs ${isUser ? 'text-right' : 'text-left'}`}
        >
          {formatTime(item.timestamp)}
        </StyledText>
      </StyledView>
    );
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {/* Header */}
      <StyledView className="flex-row items-center px-4 py-3 border-b border-borderSubtle bg-backgroundSecondary">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1">
          <Ionicons name="chevron-back-outline" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledView className="flex-1 items-center">
          <StyledText variant="body1" tw="font-semibold" color="textPrimary">Health Assistant</StyledText>
        </StyledView>
        <StyledView className="w-8" />
      </StyledView>

      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
        keyboardVerticalOffset={Platform.OS === "ios" ? 60 : 0}
      >
        <StyledView className="flex-1">
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={renderMessage}
            contentContainerStyle={{ paddingVertical: 16, paddingHorizontal: 10 }} // Adjusted horizontal padding
            showsVerticalScrollIndicator={false}
          />
          {isTyping && (
            <StyledView tw="self-start ml-3 mb-2">
              <StyledView tw="bg-backgroundSecondary px-4 py-2.5 rounded-2xl rounded-bl-lg shadow-sm flex-row items-center">
                <Ionicons name="ellipsis-horizontal" size={20} color={colors.textSecondary} />
                {/* <StyledText variant="body2" color="textSecondary">Assistant is typing...</StyledText> */}
              </StyledView>
            </StyledView>
          )}
        </StyledView>

        {/* Message Input Area */}
        <StyledView className="flex-row items-center px-3 py-2.5 border-t border-borderSubtle bg-backgroundSecondary">
          <StyledInput
            placeholder="Ask anything..."
            value={inputText}
            onChangeText={setInputText}
            multiline
            inputStyle={{ maxHeight: 100, paddingTop: Platform.OS === 'ios' ? 8 : 0, paddingBottom: Platform.OS === 'ios' ? 8 : 0 }}
            tw="flex-1 mr-2"
            onSubmitEditing={handleSendMessage}
          />
          <StyledButton
            variant={inputText.trim() === '' ? 'filledSecondary' : 'filledPrimary'}
            onPress={handleSendMessage}
            disabled={inputText.trim() === '' && !isTyping}
            tw="w-10 h-10 p-0 items-center justify-center rounded-full"
            iconNameLeft={inputText.trim() === '' ? "mic-outline" : "arrow-up-outline"}
            iconSize={22}
          >
            {null}
          </StyledButton>
        </StyledView>
      </KeyboardAvoidingView>
    </ScreenContainer>
  );
};

export default AssistantScreen;