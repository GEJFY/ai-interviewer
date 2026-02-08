'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Pause,
  Play,
  Square,
  Clock,
  MessageSquare,
  User,
  Bot,
  Loader2,
} from 'lucide-react';
import api from '@/lib/api-client';
import { createInterviewWebSocket, InterviewWebSocket, WSResponse } from '@/lib/websocket';
import { useAudioRecorder, AudioChunk } from '@/hooks/useAudioRecorder';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';

interface Message {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
}

export default function InterviewPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.id as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [currentAIResponse, setCurrentAIResponse] = useState('');
  const [elapsedTime, setElapsedTime] = useState(0);
  const [inputMode, setInputMode] = useState<'text' | 'voice'>('text');
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [transcribingText, setTranscribingText] = useState('');

  const wsRef = useRef<InterviewWebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Audio recording hook
  const {
    isRecording,
    audioLevel,
    duration: recordingDuration,
    startRecording,
    stopRecording,
  } = useAudioRecorder({
    timeSlice: 500,
    onChunk: (chunk: AudioChunk) => {
      // Send audio chunk to server for real-time transcription
      if (wsRef.current?.isConnected) {
        // Convert blob to base64 and send
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(',')[1];
          wsRef.current?.sendAudio(base64);
        };
        reader.readAsDataURL(chunk.data);
      }
    },
    onStop: async (blob: Blob, duration: number) => {
      // Final transcription will come from server
      console.log(`Recording stopped: ${duration}s`);
    },
  });

  // Audio playback hook for AI responses
  const {
    isPlaying: isAudioPlaying,
    loadBase64: playAudioBase64,
    stop: stopAudio,
    setVolume,
  } = useAudioPlayer({
    autoPlay: true,
    onEnded: () => {
      // Audio playback completed
    },
  });

  // Fetch interview details
  const { data: interview } = useQuery({
    queryKey: ['interview', interviewId],
    queryFn: () => api.interviews.get(interviewId),
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentAIResponse]);

  // Timer
  useEffect(() => {
    if (isConnected && !isPaused && !isCompleted) {
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isConnected, isPaused, isCompleted]);

  // Handle WebSocket messages
  const handleWSMessage = useCallback((response: WSResponse) => {
    switch (response.type) {
      case 'ai_response':
        if (response.payload.isPartial) {
          setCurrentAIResponse((prev) => prev + (response.payload.content || ''));
        } else if (response.payload.isFinal) {
          // Final message - add to messages
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              role: 'ai',
              content: currentAIResponse + (response.payload.content || ''),
              timestamp: new Date(),
            },
          ]);
          setCurrentAIResponse('');
          setIsLoading(false);

          // Play audio response if available and not muted
          if (response.payload.audio && !isAudioMuted) {
            playAudioBase64(response.payload.audio, 'audio/mp3');
          }
        } else {
          // Non-streaming response
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              role: 'ai',
              content: response.payload.content || '',
              timestamp: new Date(),
            },
          ]);
          setIsLoading(false);

          // Play audio response if available and not muted
          if (response.payload.audio && !isAudioMuted) {
            playAudioBase64(response.payload.audio, 'audio/mp3');
          }
        }
        break;

      case 'transcription':
        if (response.payload.speaker === 'interviewee') {
          if (response.payload.isFinal) {
            // Final transcription - add as user message
            if (response.payload.text) {
              setMessages((prev) => [
                ...prev,
                {
                  id: Date.now().toString(),
                  role: 'user',
                  content: response.payload.text!,
                  timestamp: new Date(),
                },
              ]);
              setTranscribingText('');
              setIsLoading(true);
            }
          } else {
            // Partial transcription - show in real-time
            setTranscribingText(response.payload.text || '');
          }
        }
        break;

      case 'status':
        if (response.payload.status === 'paused') {
          setIsPaused(true);
        } else if (response.payload.status === 'resumed') {
          setIsPaused(false);
        } else if (response.payload.status === 'completed') {
          setIsCompleted(true);
          setIsConnected(false);
        }
        break;

      case 'error':
        console.error('WebSocket error:', response.payload.message);
        setIsLoading(false);
        break;
    }
  }, [currentAIResponse]);

  // Connect WebSocket
  useEffect(() => {
    if (!interviewId) return;

    const ws = createInterviewWebSocket(interviewId);
    wsRef.current = ws;

    ws.onOpen = () => {
      setIsConnected(true);
    };

    ws.onClose = () => {
      setIsConnected(false);
    };

    ws.onMessage = handleWSMessage;

    ws.onError = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, [interviewId, handleWSMessage]);

  // Send message
  const sendMessage = () => {
    if (!inputValue.trim() || !wsRef.current?.isConnected || isLoading) return;

    // Add user message to UI
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: inputValue,
        timestamp: new Date(),
      },
    ]);

    // Send via WebSocket
    wsRef.current.sendMessage(inputValue);
    setInputValue('');
    setIsLoading(true);
  };

  // Pause/Resume
  const togglePause = () => {
    if (!wsRef.current?.isConnected) return;

    if (isPaused) {
      wsRef.current.sendControl('resume');
    } else {
      wsRef.current.sendControl('pause');
    }
  };

  // End interview
  const endInterview = () => {
    if (!wsRef.current?.isConnected) return;

    if (window.confirm('インタビューを終了しますか？')) {
      wsRef.current.sendControl('end');
    }
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col h-screen bg-secondary-50">
      {/* Header */}
      <header className="h-16 bg-white border-b border-secondary-200 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <MessageSquare className="w-6 h-6 text-primary-600" />
          <div>
            <h1 className="font-semibold text-secondary-900">
              {interview?.task?.name || 'インタビュー'}
            </h1>
            <p className="text-sm text-secondary-500">
              {interview?.language === 'ja' ? '日本語' : interview?.language}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Timer */}
          <div className="flex items-center gap-2 text-secondary-600">
            <Clock className="w-5 h-5" />
            <span className="font-mono">{formatTime(elapsedTime)}</span>
          </div>

          {/* Connection status */}
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              isConnected
                ? 'bg-green-100 text-green-700'
                : 'bg-secondary-100 text-secondary-700'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-secondary-400'
              }`}
            />
            {isConnected ? '接続中' : '未接続'}
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={togglePause}
              disabled={!isConnected || isCompleted}
              className="p-2 rounded-lg hover:bg-secondary-100 transition disabled:opacity-50"
              title={isPaused ? '再開' : '一時停止'}
            >
              {isPaused ? (
                <Play className="w-5 h-5 text-secondary-600" />
              ) : (
                <Pause className="w-5 h-5 text-secondary-600" />
              )}
            </button>
            <button
              onClick={endInterview}
              disabled={!isConnected || isCompleted}
              className="p-2 rounded-lg hover:bg-red-100 transition disabled:opacity-50"
              title="終了"
            >
              <Square className="w-5 h-5 text-red-600" />
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'ai'
                  ? 'bg-primary-100'
                  : 'bg-secondary-100'
              }`}
            >
              {message.role === 'ai' ? (
                <Bot className="w-5 h-5 text-primary-600" />
              ) : (
                <User className="w-5 h-5 text-secondary-600" />
              )}
            </div>
            <div
              className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                message.role === 'ai'
                  ? 'bg-white border border-secondary-200'
                  : 'bg-primary-600 text-white'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p
                className={`text-xs mt-1 ${
                  message.role === 'ai' ? 'text-secondary-400' : 'text-primary-200'
                }`}
              >
                {message.timestamp.toLocaleTimeString('ja-JP', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}

        {/* Streaming AI response */}
        {currentAIResponse && (
          <div className="flex gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-primary-100">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div className="max-w-[70%] rounded-2xl px-4 py-3 bg-white border border-secondary-200">
              <p className="whitespace-pre-wrap">{currentAIResponse}</p>
              <Loader2 className="w-4 h-4 animate-spin text-secondary-400 mt-2" />
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && !currentAIResponse && (
          <div className="flex gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-primary-100">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div className="rounded-2xl px-4 py-3 bg-white border border-secondary-200">
              <Loader2 className="w-5 h-5 animate-spin text-secondary-400" />
            </div>
          </div>
        )}

        {/* Completed message */}
        {isCompleted && (
          <div className="text-center py-8">
            <p className="text-secondary-500">インタビューが完了しました</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
            >
              ダッシュボードに戻る
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      {!isCompleted && (
        <div className="bg-white border-t border-secondary-200 p-4">
          <div className="max-w-4xl mx-auto">
            {/* Real-time transcription display */}
            {transcribingText && (
              <div className="mb-2 px-4 py-2 bg-secondary-50 rounded-lg text-secondary-600 italic">
                {transcribingText}...
              </div>
            )}

            <div className="flex gap-4 items-center">
              {/* Audio mute toggle */}
              <button
                onClick={() => {
                  setIsAudioMuted(!isAudioMuted);
                  setVolume(isAudioMuted ? 1 : 0);
                  if (!isAudioMuted && isAudioPlaying) {
                    stopAudio();
                  }
                }}
                className={`p-3 rounded-lg transition ${
                  isAudioMuted
                    ? 'bg-secondary-100 text-secondary-400'
                    : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
                }`}
                title={isAudioMuted ? '音声を有効にする' : '音声をミュート'}
              >
                {isAudioMuted ? (
                  <VolumeX className="w-5 h-5" />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </button>

              {/* Input mode: Text or Voice */}
              {inputMode === 'text' ? (
                <>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                    placeholder={
                      isPaused
                        ? 'インタビューが一時停止中です'
                        : isConnected
                        ? 'メッセージを入力...'
                        : '接続中...'
                    }
                    disabled={!isConnected || isPaused || isLoading}
                    className="flex-1 px-4 py-3 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-secondary-50 disabled:text-secondary-400"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!isConnected || isPaused || isLoading || !inputValue.trim()}
                    className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:bg-secondary-300 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Send className="w-5 h-5" />
                    送信
                  </button>
                </>
              ) : (
                <>
                  {/* Voice input mode */}
                  <div className="flex-1 flex items-center justify-center gap-4">
                    {isRecording ? (
                      <>
                        {/* Audio level visualization */}
                        <div className="flex items-center gap-1">
                          {[...Array(10)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-1 rounded-full transition-all ${
                                audioLevel * 10 > i
                                  ? 'bg-red-500'
                                  : 'bg-secondary-200'
                              }`}
                              style={{ height: `${8 + i * 2}px` }}
                            />
                          ))}
                        </div>
                        <span className="font-mono text-secondary-600">
                          {Math.floor(recordingDuration / 60)
                            .toString()
                            .padStart(2, '0')}
                          :
                          {Math.floor(recordingDuration % 60)
                            .toString()
                            .padStart(2, '0')}
                        </span>
                        <span className="text-red-500 animate-pulse">録音中</span>
                      </>
                    ) : (
                      <span className="text-secondary-500">
                        マイクボタンを押して話してください
                      </span>
                    )}
                  </div>
                  <button
                    onClick={async () => {
                      if (isRecording) {
                        await stopRecording();
                      } else {
                        await startRecording();
                      }
                    }}
                    disabled={!isConnected || isPaused}
                    className={`p-4 rounded-full transition ${
                      isRecording
                        ? 'bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/30'
                        : 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-500/30'
                    } disabled:bg-secondary-300 disabled:cursor-not-allowed`}
                  >
                    {isRecording ? (
                      <Square className="w-6 h-6" />
                    ) : (
                      <Mic className="w-6 h-6" />
                    )}
                  </button>
                </>
              )}

              {/* Toggle input mode */}
              <button
                onClick={() => {
                  if (isRecording) {
                    stopRecording();
                  }
                  setInputMode(inputMode === 'text' ? 'voice' : 'text');
                }}
                disabled={!isConnected || isPaused}
                className={`p-3 rounded-lg transition ${
                  inputMode === 'voice'
                    ? 'bg-primary-100 text-primary-600'
                    : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
                } disabled:opacity-50`}
                title={inputMode === 'text' ? '音声入力に切替' : 'テキスト入力に切替'}
              >
                {inputMode === 'text' ? (
                  <Mic className="w-5 h-5" />
                ) : (
                  <MicOff className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
