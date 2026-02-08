'use client';

/**
 * Voice input component for interview audio recording.
 *
 * Provides a microphone button with visual feedback for audio levels,
 * recording state, and permission status.
 */

import { useState, useCallback, useEffect } from 'react';
import { useAudioRecorder, AudioChunk } from '@/hooks/useAudioRecorder';

interface VoiceInputProps {
  /** Callback when audio chunk is recorded */
  onAudioChunk?: (chunk: AudioChunk) => void;
  /** Callback when recording completes */
  onRecordingComplete?: (blob: Blob, duration: number) => void;
  /** Callback for transcription text (if available) */
  onTranscription?: (text: string, isFinal: boolean) => void;
  /** Whether voice input is disabled */
  disabled?: boolean;
  /** Button size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS class */
  className?: string;
}

const sizeClasses = {
  sm: 'w-10 h-10',
  md: 'w-14 h-14',
  lg: 'w-20 h-20',
};

const iconSizes = {
  sm: 'w-5 h-5',
  md: 'w-7 h-7',
  lg: 'w-10 h-10',
};

export function VoiceInput({
  onAudioChunk,
  onRecordingComplete,
  onTranscription,
  disabled = false,
  size = 'md',
  className = '',
}: VoiceInputProps) {
  const [showPermissionPrompt, setShowPermissionPrompt] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    state,
    isRecording,
    hasPermission,
    audioLevel,
    duration,
    startRecording,
    stopRecording,
    requestPermission,
  } = useAudioRecorder({
    timeSlice: 500, // Send chunks every 500ms for real-time transcription
    onChunk: onAudioChunk,
    onStop: onRecordingComplete,
    onError: (error) => {
      console.error('Recording error:', error);
      setErrorMessage('マイクへのアクセスに失敗しました');
    },
  });

  // Check permission on mount
  useEffect(() => {
    if (hasPermission === null) {
      requestPermission().then(granted => {
        if (!granted) {
          setShowPermissionPrompt(true);
        }
      });
    }
  }, [hasPermission, requestPermission]);

  const handleClick = useCallback(async () => {
    if (disabled) return;

    setErrorMessage(null);

    if (isRecording) {
      await stopRecording();
    } else {
      if (hasPermission === false) {
        setShowPermissionPrompt(true);
        return;
      }
      await startRecording();
    }
  }, [disabled, isRecording, hasPermission, startRecording, stopRecording]);

  const handlePermissionRequest = useCallback(async () => {
    const granted = await requestPermission();
    setShowPermissionPrompt(false);
    if (granted) {
      await startRecording();
    }
  }, [requestPermission, startRecording]);

  // Format duration as MM:SS
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate ring size based on audio level
  const ringScale = 1 + audioLevel * 0.5;

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      {/* Permission prompt modal */}
      {showPermissionPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              マイクへのアクセスを許可
            </h3>
            <p className="text-gray-600 mb-4">
              音声入力を使用するには、マイクへのアクセスを許可してください。
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowPermissionPrompt(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                キャンセル
              </button>
              <button
                onClick={handlePermissionRequest}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                許可する
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Microphone button */}
      <div className="relative">
        {/* Audio level ring */}
        {isRecording && (
          <div
            className="absolute inset-0 rounded-full bg-red-500/20 transition-transform"
            style={{
              transform: `scale(${ringScale})`,
            }}
          />
        )}

        <button
          onClick={handleClick}
          disabled={disabled || state === 'processing'}
          className={`
            relative z-10 rounded-full flex items-center justify-center
            transition-all duration-200
            ${sizeClasses[size]}
            ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/30'
                : disabled
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/30'
            }
          `}
          aria-label={isRecording ? '録音停止' : '録音開始'}
        >
          {state === 'processing' ? (
            // Loading spinner
            <svg
              className={`animate-spin ${iconSizes[size]}`}
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : isRecording ? (
            // Stop icon
            <svg
              className={iconSizes[size]}
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
          ) : (
            // Microphone icon
            <svg
              className={iconSizes[size]}
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          )}
        </button>
      </div>

      {/* Duration display */}
      {isRecording && (
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="font-mono text-gray-700">{formatDuration(duration)}</span>
        </div>
      )}

      {/* Error message */}
      {errorMessage && (
        <p className="text-red-500 text-sm">{errorMessage}</p>
      )}

      {/* Permission status */}
      {hasPermission === false && !showPermissionPrompt && (
        <button
          onClick={() => setShowPermissionPrompt(true)}
          className="text-sm text-blue-600 hover:underline"
        >
          マイクを有効にする
        </button>
      )}
    </div>
  );
}

export default VoiceInput;
