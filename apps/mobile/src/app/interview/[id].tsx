/**
 * Interview screen with voice input and chat interface.
 */

import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';

interface Message {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
}

export default function InterviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: 'こんにちは。本日はお時間をいただきありがとうございます。月次決算プロセスについてお伺いさせてください。まず、月次決算の全体的な流れを教えていただけますか？',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [inputMode, setInputMode] = useState<'text' | 'voice'>('text');

  const flatListRef = useRef<FlatList>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Request audio permissions
  useEffect(() => {
    (async () => {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('権限エラー', 'マイクへのアクセスを許可してください。');
      }
    })();

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  const startRecording = async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      await recording.startAsync();

      recordingRef.current = recording;
      setIsRecording(true);
      setRecordingDuration(0);

      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('エラー', '録音を開始できませんでした。');
    }
  };

  const stopRecording = async () => {
    if (!recordingRef.current) return;

    try {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;
      setIsRecording(false);

      if (uri) {
        // Simulate sending audio for transcription
        setIsLoading(true);
        setTimeout(() => {
          // Mock transcription result
          const mockTranscription = '毎月5営業日までに前月分の決算を締めています。';
          handleSendMessage(mockTranscription);
          setIsLoading(false);
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      setIsRecording(false);
    }
  };

  const handleSendMessage = (text: string) => {
    if (!text.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'なるほど、毎月5営業日までに締められているのですね。その決算処理において、特に時間がかかる作業や、手作業で行っている部分はありますか？',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, 2000);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleEndInterview = () => {
    Alert.alert(
      'インタビュー終了',
      'インタビューを終了しますか？',
      [
        { text: 'キャンセル', style: 'cancel' },
        { text: '終了', style: 'destructive', onPress: () => router.back() },
      ]
    );
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View
      style={[
        styles.messageContainer,
        item.role === 'user' ? styles.userMessage : styles.aiMessage,
      ]}
    >
      <View
        style={[
          styles.avatar,
          item.role === 'user' ? styles.userAvatar : styles.aiAvatar,
        ]}
      >
        <Ionicons
          name={item.role === 'user' ? 'person' : 'chatbubble-ellipses'}
          size={16}
          color="#fff"
        />
      </View>
      <View
        style={[
          styles.messageBubble,
          item.role === 'user' ? styles.userBubble : styles.aiBubble,
        ]}
      >
        <Text
          style={[
            styles.messageText,
            item.role === 'user' && styles.userText,
          ]}
        >
          {item.content}
        </Text>
        <Text style={styles.timestamp}>
          {item.timestamp.toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </Text>
      </View>
    </View>
  );

  return (
    <>
      <Stack.Screen
        options={{
          title: '月次決算プロセス',
          headerRight: () => (
            <TouchableOpacity onPress={handleEndInterview}>
              <Ionicons name="stop-circle" size={28} color="#fff" />
            </TouchableOpacity>
          ),
        }}
      />

      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          ListFooterComponent={
            isLoading ? (
              <View style={[styles.messageContainer, styles.aiMessage]}>
                <View style={[styles.avatar, styles.aiAvatar]}>
                  <Ionicons name="chatbubble-ellipses" size={16} color="#fff" />
                </View>
                <View style={[styles.messageBubble, styles.aiBubble]}>
                  <Text style={styles.loadingDots}>...</Text>
                </View>
              </View>
            ) : null
          }
        />

        {/* Input Area */}
        <View style={styles.inputArea}>
          {inputMode === 'text' ? (
            <View style={styles.textInputContainer}>
              <TextInput
                style={styles.textInput}
                value={inputText}
                onChangeText={setInputText}
                placeholder="メッセージを入力..."
                placeholderTextColor="#9ca3af"
                multiline
                maxLength={1000}
              />
              <TouchableOpacity
                style={[
                  styles.sendButton,
                  !inputText.trim() && styles.sendButtonDisabled,
                ]}
                onPress={() => handleSendMessage(inputText)}
                disabled={!inputText.trim() || isLoading}
              >
                <Ionicons name="send" size={20} color="#fff" />
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.voiceInputContainer}>
              {isRecording ? (
                <>
                  <View style={styles.recordingIndicator}>
                    <View style={styles.recordingDot} />
                    <Text style={styles.recordingText}>録音中</Text>
                    <Text style={styles.recordingTime}>
                      {formatDuration(recordingDuration)}
                    </Text>
                  </View>
                  <TouchableOpacity
                    style={styles.stopButton}
                    onPress={stopRecording}
                  >
                    <Ionicons name="stop" size={28} color="#fff" />
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <Text style={styles.voiceHint}>
                    マイクボタンを押して話してください
                  </Text>
                  <TouchableOpacity
                    style={styles.micButton}
                    onPress={startRecording}
                    disabled={isLoading}
                  >
                    <Ionicons name="mic" size={28} color="#fff" />
                  </TouchableOpacity>
                </>
              )}
            </View>
          )}

          {/* Mode Toggle */}
          <TouchableOpacity
            style={styles.modeToggle}
            onPress={() => setInputMode(inputMode === 'text' ? 'voice' : 'text')}
          >
            <Ionicons
              name={inputMode === 'text' ? 'mic-outline' : 'chatbubble-outline'}
              size={22}
              color="#6b7280"
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  messageList: {
    padding: 16,
    paddingBottom: 8,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    maxWidth: '85%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
  },
  aiMessage: {
    alignSelf: 'flex-start',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
  },
  userAvatar: {
    backgroundColor: '#6b7280',
  },
  aiAvatar: {
    backgroundColor: '#2563eb',
  },
  messageBubble: {
    borderRadius: 16,
    padding: 12,
    maxWidth: '100%',
  },
  userBubble: {
    backgroundColor: '#2563eb',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#1f2937',
  },
  userText: {
    color: '#fff',
  },
  timestamp: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  loadingDots: {
    fontSize: 24,
    color: '#9ca3af',
    letterSpacing: 4,
  },
  inputArea: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  textInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#f3f4f6',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
  },
  textInput: {
    flex: 1,
    fontSize: 15,
    maxHeight: 100,
    color: '#1f2937',
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#d1d5db',
  },
  voiceInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  recordingIndicator: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  recordingDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ef4444',
    marginRight: 8,
  },
  recordingText: {
    color: '#ef4444',
    fontWeight: '600',
    marginRight: 8,
  },
  recordingTime: {
    color: '#6b7280',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  voiceHint: {
    flex: 1,
    color: '#9ca3af',
    textAlign: 'center',
  },
  micButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#2563eb',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  stopButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modeToggle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
