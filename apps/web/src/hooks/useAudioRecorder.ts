/**
 * Custom hook for audio recording with Web Audio API.
 *
 * Provides functionality for recording audio from microphone,
 * with real-time audio level monitoring and chunk-based streaming.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import logger from '@/lib/logger';

export type RecordingState = 'idle' | 'recording' | 'paused' | 'processing';

export interface AudioChunk {
  data: Blob;
  timestamp: number;
  duration: number;
}

export interface UseAudioRecorderOptions {
  /** Audio MIME type (default: 'audio/webm;codecs=opus') */
  mimeType?: string;
  /** Time slice for chunked recording in ms (default: 1000) */
  timeSlice?: number;
  /** Sample rate (default: 16000 for speech recognition) */
  sampleRate?: number;
  /** Callback when audio chunk is available */
  onChunk?: (chunk: AudioChunk) => void;
  /** Callback for audio level updates (0-1 range) */
  onAudioLevel?: (level: number) => void;
  /** Callback when recording starts */
  onStart?: () => void;
  /** Callback when recording stops */
  onStop?: (blob: Blob, duration: number) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

export interface UseAudioRecorderReturn {
  /** Current recording state */
  state: RecordingState;
  /** Whether currently recording */
  isRecording: boolean;
  /** Whether microphone permission is granted */
  hasPermission: boolean | null;
  /** Current audio level (0-1) */
  audioLevel: number;
  /** Recording duration in seconds */
  duration: number;
  /** Start recording */
  startRecording: () => Promise<void>;
  /** Stop recording */
  stopRecording: () => Promise<Blob | null>;
  /** Pause recording */
  pauseRecording: () => void;
  /** Resume recording */
  resumeRecording: () => void;
  /** Request microphone permission */
  requestPermission: () => Promise<boolean>;
}

export function useAudioRecorder(
  options: UseAudioRecorderOptions = {}
): UseAudioRecorderReturn {
  const {
    mimeType = 'audio/webm;codecs=opus',
    timeSlice = 1000,
    sampleRate = 16000,
    onChunk,
    onAudioLevel,
    onStart,
    onStop,
    onError,
  } = options;

  const [state, setState] = useState<RecordingState>('idle');
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [duration, setDuration] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Check if browser supports required APIs
  const isSupported = typeof window !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    typeof navigator.mediaDevices !== 'undefined' &&
    typeof MediaRecorder !== 'undefined';

  // Request microphone permission
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!isSupported) {
      setHasPermission(false);
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Stop the test stream
      stream.getTracks().forEach(track => track.stop());
      setHasPermission(true);
      return true;
    } catch (error) {
      logger.error('Microphone permission denied:', error);
      setHasPermission(false);
      onError?.(error as Error);
      return false;
    }
  }, [isSupported, sampleRate, onError]);

  // Monitor audio levels
  const startAudioLevelMonitoring = useCallback((stream: MediaStream) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext();
    }

    const audioContext = audioContextRef.current;
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyserRef.current = analyser;

    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const updateLevel = () => {
      if (state !== 'recording') return;

      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      const normalizedLevel = Math.min(average / 128, 1);
      setAudioLevel(normalizedLevel);
      onAudioLevel?.(normalizedLevel);

      animationFrameRef.current = requestAnimationFrame(updateLevel);
    };

    updateLevel();
  }, [state, onAudioLevel]);

  // Stop audio level monitoring
  const stopAudioLevelMonitoring = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    if (!isSupported) {
      onError?.(new Error('Audio recording not supported'));
      return;
    }

    try {
      setState('processing');

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;
      setHasPermission(true);

      // Check for supported MIME type
      const supportedMimeType = MediaRecorder.isTypeSupported(mimeType)
        ? mimeType
        : 'audio/webm';

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: supportedMimeType,
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      startTimeRef.current = Date.now();

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);

          const chunk: AudioChunk = {
            data: event.data,
            timestamp: Date.now() - startTimeRef.current,
            duration: timeSlice,
          };
          onChunk?.(chunk);
        }
      };

      mediaRecorder.onstart = () => {
        setState('recording');
        onStart?.();

        // Start duration timer
        durationIntervalRef.current = setInterval(() => {
          setDuration((Date.now() - startTimeRef.current) / 1000);
        }, 100);
      };

      mediaRecorder.onstop = () => {
        // Clear duration timer
        if (durationIntervalRef.current) {
          clearInterval(durationIntervalRef.current);
          durationIntervalRef.current = null;
        }

        const blob = new Blob(chunksRef.current, { type: supportedMimeType });
        const totalDuration = (Date.now() - startTimeRef.current) / 1000;
        onStop?.(blob, totalDuration);
      };

      mediaRecorder.onerror = (event) => {
        logger.error('MediaRecorder error:', event);
        onError?.(new Error('Recording error'));
        setState('idle');
      };

      // Start recording with time slicing
      mediaRecorder.start(timeSlice);
      startAudioLevelMonitoring(stream);

    } catch (error) {
      logger.error('Failed to start recording:', error);
      setState('idle');
      setHasPermission(false);
      onError?.(error as Error);
    }
  }, [
    isSupported,
    mimeType,
    sampleRate,
    timeSlice,
    onChunk,
    onStart,
    onStop,
    onError,
    startAudioLevelMonitoring,
  ]);

  // Stop recording
  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || state !== 'recording') {
        resolve(null);
        return;
      }

      const mediaRecorder = mediaRecorderRef.current;

      mediaRecorder.onstop = () => {
        if (durationIntervalRef.current) {
          clearInterval(durationIntervalRef.current);
          durationIntervalRef.current = null;
        }

        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        const totalDuration = (Date.now() - startTimeRef.current) / 1000;

        // Stop audio monitoring
        stopAudioLevelMonitoring();

        // Stop all tracks
        streamRef.current?.getTracks().forEach(track => track.stop());
        streamRef.current = null;

        setState('idle');
        setDuration(0);
        onStop?.(blob, totalDuration);
        resolve(blob);
      };

      mediaRecorder.stop();
    });
  }, [state, onStop, stopAudioLevelMonitoring]);

  // Pause recording
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.pause();
      setState('paused');
      stopAudioLevelMonitoring();
    }
  }, [stopAudioLevelMonitoring]);

  // Resume recording
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'paused') {
      mediaRecorderRef.current.resume();
      setState('recording');
      if (streamRef.current) {
        startAudioLevelMonitoring(streamRef.current);
      }
    }
  }, [startAudioLevelMonitoring]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudioLevelMonitoring();
      streamRef.current?.getTracks().forEach(track => track.stop());
      audioContextRef.current?.close();

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [stopAudioLevelMonitoring]);

  return {
    state,
    isRecording: state === 'recording',
    hasPermission,
    audioLevel,
    duration,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    requestPermission,
  };
}
