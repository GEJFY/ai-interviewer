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
  Zap,
  ArrowLeft,
} from 'lucide-react';
import { cn } from '@/lib/cn';
import logger from '@/lib/logger';
import { Badge } from '@/components/ui/badge';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
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
  const [isEndDialogOpen, setIsEndDialogOpen] = useState(false);

  const wsRef = useRef<InterviewWebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const {
    isRecording,
    audioLevel,
    duration: recordingDuration,
    startRecording,
    stopRecording,
  } = useAudioRecorder({
    timeSlice: 500,
    onChunk: (chunk: AudioChunk) => {
      if (wsRef.current?.isConnected) {
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(',')[1];
          wsRef.current?.sendAudio(base64);
        };
        reader.readAsDataURL(chunk.data);
      }
    },
    onStop: async (_blob: Blob, _duration: number) => {
      // Recording stopped - blob available for further processing if needed
    },
  });

  const {
    isPlaying: isAudioPlaying,
    loadBase64: playAudioBase64,
    stop: stopAudio,
    setVolume,
  } = useAudioPlayer({
    autoPlay: true,
    onEnded: () => {},
  });

  const { data: interview } = useQuery({
    queryKey: ['interview', interviewId],
    queryFn: () => api.interviews.get(interviewId),
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentAIResponse]);

  useEffect(() => {
    if (isConnected && !isPaused && !isCompleted) {
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isConnected, isPaused, isCompleted]);

  const handleWSMessage = useCallback((response: WSResponse) => {
    switch (response.type) {
      case 'ai_response':
        if (response.payload.isPartial) {
          setCurrentAIResponse((prev) => prev + (response.payload.content || ''));
        } else if (response.payload.isFinal) {
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
          if (response.payload.audio && !isAudioMuted) {
            playAudioBase64(response.payload.audio, 'audio/mp3');
          }
        } else {
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
          if (response.payload.audio && !isAudioMuted) {
            playAudioBase64(response.payload.audio, 'audio/mp3');
          }
        }
        break;

      case 'transcription':
        if (response.payload.speaker === 'interviewee') {
          if (response.payload.isFinal) {
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
            setTranscribingText(response.payload.text || '');
          }
        }
        break;

      case 'status':
        if (response.payload.status === 'paused') setIsPaused(true);
        else if (response.payload.status === 'resumed') setIsPaused(false);
        else if (response.payload.status === 'completed') {
          setIsCompleted(true);
          setIsConnected(false);
        }
        break;

      case 'error':
        logger.error('WebSocket error:', response.payload.message);
        setIsLoading(false);
        break;
    }
  }, [currentAIResponse]);

  useEffect(() => {
    if (!interviewId) return;
    const ws = createInterviewWebSocket(interviewId);
    wsRef.current = ws;
    ws.onOpen = () => setIsConnected(true);
    ws.onClose = () => setIsConnected(false);
    ws.onMessage = handleWSMessage;
    ws.onError = (error) => logger.error('WebSocket error:', error);
    ws.connect();
    return () => ws.disconnect();
  }, [interviewId, handleWSMessage]);

  const sendMessage = () => {
    if (!inputValue.trim() || !wsRef.current?.isConnected || isLoading) return;
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: 'user', content: inputValue, timestamp: new Date() },
    ]);
    wsRef.current.sendMessage(inputValue);
    setInputValue('');
    setIsLoading(true);
  };

  const togglePause = () => {
    if (!wsRef.current?.isConnected) return;
    wsRef.current.sendControl(isPaused ? 'resume' : 'pause');
  };

  const endInterview = () => {
    if (!wsRef.current?.isConnected) return;
    setIsEndDialogOpen(true);
  };

  const confirmEndInterview = () => {
    wsRef.current?.sendControl('end');
    setIsEndDialogOpen(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col h-screen bg-[rgb(var(--bg))]">
      {/* ヘッダー */}
      <header className="h-16 glass-strong border-b border-surface-200 dark:border-surface-800 flex items-center justify-between px-6 z-10">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-accent-500/10 flex items-center justify-center">
            <Zap className="w-4 h-4 text-accent-500" />
          </div>
          <div>
            <h1 className="font-semibold text-surface-900 dark:text-surface-50 text-sm">
              {interview?.task?.name || 'インタビュー'}
            </h1>
            <p className="text-xs text-surface-400">
              {interview?.language === 'ja' ? '日本語' : interview?.language}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* タイマー */}
          <div className="flex items-center gap-2 text-surface-500 dark:text-surface-400">
            <Clock className="w-4 h-4" />
            <span className="font-mono text-sm">{formatTime(elapsedTime)}</span>
          </div>

          {/* 接続ステータス */}
          <Badge variant={isConnected ? 'success' : 'default'}>
            <span className="flex items-center gap-1.5">
              <span className={cn(
                'w-1.5 h-1.5 rounded-full',
                isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-surface-400'
              )} />
              {isConnected ? '接続中' : '未接続'}
            </span>
          </Badge>

          {/* コントロール */}
          <div className="flex items-center gap-1 ml-2">
            <button
              onClick={togglePause}
              disabled={!isConnected || isCompleted}
              className="p-2 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors disabled:opacity-50"
              title={isPaused ? '再開' : '一時停止'}
            >
              {isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
            </button>
            <button
              onClick={endInterview}
              disabled={!isConnected || isCompleted}
              className="p-2 rounded-lg text-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
              title="終了"
            >
              <Square className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* メッセージエリア */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn('flex gap-3', message.role === 'user' && 'flex-row-reverse')}
            >
              <div
                className={cn(
                  'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                  message.role === 'ai'
                    ? 'bg-accent-500/10'
                    : 'bg-surface-100 dark:bg-surface-800'
                )}
              >
                {message.role === 'ai' ? (
                  <Zap className="w-4 h-4 text-accent-500" />
                ) : (
                  <User className="w-4 h-4 text-surface-500" />
                )}
              </div>
              <div
                className={cn(
                  'max-w-[70%] rounded-2xl px-4 py-3',
                  message.role === 'ai'
                    ? 'glass rounded-tl-sm'
                    : 'bg-accent-500/10 dark:bg-accent-500/20 rounded-tr-sm'
                )}
              >
                <p className="whitespace-pre-wrap text-surface-800 dark:text-surface-200 text-sm leading-relaxed">
                  {message.content}
                </p>
                <p className="text-[10px] mt-1.5 text-surface-400">
                  {message.timestamp.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* ストリーミング中のAI応答 */}
          {currentAIResponse && (
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-accent-500/10">
                <Zap className="w-4 h-4 text-accent-500" />
              </div>
              <div className="max-w-[70%] glass rounded-2xl rounded-tl-sm px-4 py-3">
                <p className="whitespace-pre-wrap text-surface-800 dark:text-surface-200 text-sm leading-relaxed">
                  {currentAIResponse}
                </p>
                <Loader2 className="w-3 h-3 animate-spin text-accent-500 mt-2" />
              </div>
            </div>
          )}

          {/* ローディング */}
          {isLoading && !currentAIResponse && (
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-accent-500/10">
                <Zap className="w-4 h-4 text-accent-500" />
              </div>
              <div className="glass rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex items-center gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 bg-accent-500 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 完了メッセージ */}
          {isCompleted && (
            <div className="text-center py-12">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-6 h-6 text-emerald-500" />
              </div>
              <p className="text-surface-500 dark:text-surface-400 mb-4">インタビューが完了しました</p>
              <button
                onClick={() => router.push('/dashboard')}
                className="px-6 py-2.5 bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-lg font-medium hover:from-accent-600 hover:to-accent-700 transition-all shadow-lg shadow-accent-500/20"
              >
                ダッシュボードに戻る
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 入力エリア */}
      {!isCompleted && (
        <div className="border-t border-surface-200 dark:border-surface-800 bg-[rgb(var(--bg-elevated))] p-4">
          <div className="max-w-3xl mx-auto">
            {/* リアルタイム文字起こし */}
            {transcribingText && (
              <div className="mb-2 px-4 py-2 bg-surface-50 dark:bg-surface-800 rounded-lg text-surface-500 dark:text-surface-400 text-sm italic">
                {transcribingText}...
              </div>
            )}

            <div className="flex gap-3 items-center">
              {/* 音声ミュート */}
              <button
                onClick={() => {
                  setIsAudioMuted(!isAudioMuted);
                  setVolume(isAudioMuted ? 1 : 0);
                  if (!isAudioMuted && isAudioPlaying) stopAudio();
                }}
                className={cn(
                  'p-2.5 rounded-lg transition-colors',
                  isAudioMuted
                    ? 'text-surface-400 bg-surface-100 dark:bg-surface-800'
                    : 'text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800'
                )}
                title={isAudioMuted ? '音声を有効にする' : '音声をミュート'}
              >
                {isAudioMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>

              {/* テキスト / 音声入力 */}
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
                      isPaused ? '一時停止中...' : isConnected ? 'メッセージを入力...' : '接続中...'
                    }
                    disabled={!isConnected || isPaused || isLoading}
                    className="flex-1 px-4 py-3 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-xl text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 disabled:opacity-50 transition-all text-sm"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!isConnected || isPaused || isLoading || !inputValue.trim()}
                    className="px-5 py-3 bg-gradient-to-r from-accent-500 to-accent-600 text-white rounded-xl hover:from-accent-600 hover:to-accent-700 transition-all shadow-lg shadow-accent-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 font-medium text-sm"
                  >
                    <Send className="w-4 h-4" />
                    送信
                  </button>
                </>
              ) : (
                <>
                  <div className="flex-1 flex items-center justify-center gap-4">
                    {isRecording ? (
                      <>
                        <div className="flex items-center gap-0.5">
                          {[...Array(10)].map((_, i) => (
                            <div
                              key={i}
                              className={cn(
                                'w-1 rounded-full transition-all',
                                audioLevel * 10 > i ? 'bg-red-500' : 'bg-surface-200 dark:bg-surface-700'
                              )}
                              style={{ height: `${8 + i * 2}px` }}
                            />
                          ))}
                        </div>
                        <span className="font-mono text-sm text-surface-500 dark:text-surface-400">
                          {Math.floor(recordingDuration / 60).toString().padStart(2, '0')}:
                          {Math.floor(recordingDuration % 60).toString().padStart(2, '0')}
                        </span>
                        <span className="text-red-500 text-sm animate-pulse">録音中</span>
                      </>
                    ) : (
                      <span className="text-surface-400 text-sm">マイクボタンを押して話してください</span>
                    )}
                  </div>
                  <button
                    onClick={async () => {
                      if (isRecording) await stopRecording();
                      else await startRecording();
                    }}
                    disabled={!isConnected || isPaused}
                    className={cn(
                      'p-3.5 rounded-full transition-all disabled:opacity-40 disabled:cursor-not-allowed',
                      isRecording
                        ? 'bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/30'
                        : 'bg-gradient-to-r from-accent-500 to-accent-600 text-white hover:from-accent-600 hover:to-accent-700 shadow-lg shadow-accent-500/25'
                    )}
                  >
                    {isRecording ? <Square className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  </button>
                </>
              )}

              {/* 入力モード切替 */}
              <button
                onClick={() => {
                  if (isRecording) stopRecording();
                  setInputMode(inputMode === 'text' ? 'voice' : 'text');
                }}
                disabled={!isConnected || isPaused}
                className={cn(
                  'p-2.5 rounded-lg transition-colors disabled:opacity-50',
                  inputMode === 'voice'
                    ? 'bg-accent-500/10 text-accent-500'
                    : 'text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800'
                )}
                title={inputMode === 'text' ? '音声入力に切替' : 'テキスト入力に切替'}
              >
                {inputMode === 'text' ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        isOpen={isEndDialogOpen}
        onClose={() => setIsEndDialogOpen(false)}
        onConfirm={confirmEndInterview}
        title="インタビュー終了"
        message="インタビューを終了しますか？終了後は再開できません。"
        confirmLabel="終了する"
        variant="warning"
      />
    </div>
  );
}
