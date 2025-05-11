import React, { useState, useRef } from 'react';
import { View, FlatList, KeyboardAvoidingView, Platform, TouchableOpacity, TextInput } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import { Send, ArrowLeft, Bot } from 'lucide-react-native';
import { useTheme } from '../../theme';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledInput from '../../components/common/StyledInput';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledTextInputCustom = styled(TextInput);

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

type AssistantScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Assistant'>;

const AssistantScreen = () => {
  const navigation = useNavigation<AssistantScreenNavigationProp>();
  const theme = useTheme();
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
    
    // Simulate assistant response
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

  // Get a relevant response based on user's input
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

  // Scroll to end when messages change
  React.useEffect(() => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  // Render a chat bubble
  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.sender === 'user';
    
    return (
      <StyledView 
        // Dynamic styling for user vs. assistant messages
        tw={`my-1.5 mx-2 max-w-[80%] rounded-2xl ${
          isUser 
            ? 'bg-primary self-end rounded-br-md'  // User: Primary color, right, specific corner rounded
            : 'bg-gray-200 self-start rounded-bl-md' // Assistant: Gray, left, specific corner rounded
        }`}
        style={{
          // Adding distinct border radius for a more modern bubble feel
          borderTopLeftRadius: isUser ? 16 : 4,
          borderTopRightRadius: isUser ? 4 : 16,
          borderBottomLeftRadius: 16,
          borderBottomRightRadius: 16,
          paddingHorizontal: 14, // Increased padding
          paddingVertical: 10,
        }}
      >
        {!isUser && (
          <StyledView tw="flex-row items-center mb-1.5">
            <Bot size={16} color={isUser ? "#FFFFFF" : "#0EA5E9"} />
            <StyledText variant="label" tw="ml-1.5 font-medium" color={isUser ? "white" : "primaryDark"}>
              Health Assistant
            </StyledText>
          </StyledView>
        )}
        
        <StyledText 
          variant="body1" 
          style={{ lineHeight: 20 }} // Improved line height for readability
          tw={isUser ? 'text-white' : 'text-gray-800'}
        >
          {item.text}
        </StyledText>
        
        <StyledText 
          variant="caption" 
          tw={`mt-1.5 text-xs ${isUser ? 'text-white/80 text-right' : 'text-gray-500 text-left'}`}
        >
          {formatTime(item.timestamp)}
        </StyledText>
      </StyledView>
    );
  };

  // Format timestamp to display only time (e.g., "2:30 PM")
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={theme.colors.backgroundScreen}>
      {/* Header */}
      <StyledView tw="flex-row items-center px-4 py-3 border-b border-gray-200 bg-white">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} >
          <ArrowLeft size={24} color="#6B7280" />
        </StyledTouchableOpacity>
        <StyledView tw="flex-1 items-center">
          <StyledText variant="h3" color="primary">Health Assistant</StyledText>
        </StyledView>
        <StyledView tw="w-6" /> {/* Space balancer for header */}
      </StyledView>

      {/* Chat Area */}
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1, backgroundColor: theme.colors.backgroundScreen }}
        keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
      >
        <StyledView tw="flex-1">
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={renderMessage}
            contentContainerStyle={{ paddingVertical: 16, paddingHorizontal: 8 }} // Added horizontal padding
            showsVerticalScrollIndicator={false}
          />

          {/* Typing indicator */}
          {isTyping && (
            <StyledView tw="flex-row items-center px-4 py-3 mb-1 ml-2 self-start">
              <StyledView tw="bg-gray-200 px-4 py-2.5 rounded-full flex-row items-center rounded-bl-md">
                <Bot size={14} color="#0EA5E9" style={{marginRight: 6}}/>
                <StyledText variant="body2" color="textSecondary">Assistant is typing...</StyledText>
              </StyledView>
            </StyledView>
          )}
        </StyledView>

        {/* Message Input Area */}
        <StyledView tw="px-3 py-2.5 border-t border-gray-200 bg-white">
          <StyledView tw="flex-row items-center">
            <StyledTextInputCustom
              tw="flex-1 py-2.5 px-4 bg-gray-100 rounded-full mr-2 border border-gray-200"
              placeholder="Ask MedInsight..."
              value={inputText}
              onChangeText={setInputText}
              multiline
              style={{ maxHeight: 120, fontSize: 16, lineHeight: 20 }}
              placeholderTextColor="#9CA3AF"
              onSubmitEditing={handleSendMessage}
              blurOnSubmit={Platform.OS === 'android'} // Keep true for Android, false for iOS to allow easy resend
            />
            <StyledTouchableOpacity 
              tw={`p-2.5 rounded-full ${
                inputText.trim() === '' ? 'bg-gray-300' : 'bg-primary'
              }`}
              onPress={handleSendMessage}
              disabled={inputText.trim() === ''}
            >
              <Send size={22} color="#FFFFFF" />
            </StyledTouchableOpacity>
          </StyledView>
        </StyledView>
      </KeyboardAvoidingView>
    </ScreenContainer>
  );
};

export default AssistantScreen;