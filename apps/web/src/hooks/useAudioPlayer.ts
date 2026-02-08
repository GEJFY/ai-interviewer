/**
 * Custom hook for audio playback.
 *
 * Provides functionality for playing audio responses from the AI,
 * with support for queued playback and streaming audio.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

export type PlaybackState = 'idle' | 'loading' | 'playing' | 'paused' | 'ended';

export interface UseAudioPlayerOptions {
  /** Volume level (0-1, default: 1) */
  volume?: number;
  /** Playback rate (0.5-2, default: 1) */
  playbackRate?: number;
  /** Auto-play when audio is loaded */
  autoPlay?: boolean;
  /** Callback when playback starts */
  onPlay?: () => void;
  /** Callback when playback pauses */
  onPause?: () => void;
  /** Callback when playback ends */
  onEnded?: () => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Callback for progress updates */
  onProgress?: (currentTime: number, duration: number) => void;
}

export interface UseAudioPlayerReturn {
  /** Current playback state */
  state: PlaybackState;
  /** Whether currently playing */
  isPlaying: boolean;
  /** Current playback time in seconds */
  currentTime: number;
  /** Total duration in seconds */
  duration: number;
  /** Current volume (0-1) */
  volume: number;
  /** Load and optionally play audio from URL */
  loadAudio: (url: string) => Promise<void>;
  /** Load and optionally play audio from blob */
  loadBlob: (blob: Blob) => Promise<void>;
  /** Load and optionally play audio from base64 */
  loadBase64: (base64: string, mimeType?: string) => Promise<void>;
  /** Start or resume playback */
  play: () => Promise<void>;
  /** Pause playback */
  pause: () => void;
  /** Stop playback and reset */
  stop: () => void;
  /** Seek to position (0-1 range) */
  seek: (position: number) => void;
  /** Set volume (0-1 range) */
  setVolume: (volume: number) => void;
  /** Set playback rate (0.5-2 range) */
  setPlaybackRate: (rate: number) => void;
  /** Queue audio for sequential playback */
  queue: (url: string) => void;
  /** Clear the playback queue */
  clearQueue: () => void;
}

export function useAudioPlayer(
  options: UseAudioPlayerOptions = {}
): UseAudioPlayerReturn {
  const {
    volume: initialVolume = 1,
    playbackRate: initialPlaybackRate = 1,
    autoPlay = false,
    onPlay,
    onPause,
    onEnded,
    onError,
    onProgress,
  } = options;

  const [state, setState] = useState<PlaybackState>('idle');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(initialVolume);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const queueRef = useRef<string[]>([]);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize audio element
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const audio = new Audio();
    audio.volume = initialVolume;
    audio.playbackRate = initialPlaybackRate;
    audioRef.current = audio;

    // Event listeners
    audio.onloadstart = () => setState('loading');
    audio.oncanplay = () => {
      if (state === 'loading') {
        setState('idle');
        if (autoPlay) {
          audio.play().catch(console.error);
        }
      }
    };
    audio.onplay = () => {
      setState('playing');
      onPlay?.();
      startProgressTracking();
    };
    audio.onpause = () => {
      setState('paused');
      onPause?.();
      stopProgressTracking();
    };
    audio.onended = () => {
      setState('ended');
      onEnded?.();
      stopProgressTracking();
      playNext();
    };
    audio.onerror = () => {
      setState('idle');
      onError?.(new Error('Audio playback error'));
      stopProgressTracking();
    };
    audio.ondurationchange = () => {
      setDuration(audio.duration);
    };

    return () => {
      audio.pause();
      audio.src = '';
      stopProgressTracking();
    };
  }, []);

  // Progress tracking
  const startProgressTracking = useCallback(() => {
    if (progressIntervalRef.current) return;

    progressIntervalRef.current = setInterval(() => {
      if (audioRef.current) {
        const time = audioRef.current.currentTime;
        const dur = audioRef.current.duration;
        setCurrentTime(time);
        onProgress?.(time, dur);
      }
    }, 100);
  }, [onProgress]);

  const stopProgressTracking = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  }, []);

  // Play next in queue
  const playNext = useCallback(async () => {
    if (queueRef.current.length > 0) {
      const nextUrl = queueRef.current.shift()!;
      await loadAudio(nextUrl);
    }
  }, []);

  // Load audio from URL
  const loadAudio = useCallback(async (url: string) => {
    if (!audioRef.current) return;

    setState('loading');
    audioRef.current.src = url;
    audioRef.current.load();

    if (autoPlay) {
      try {
        await audioRef.current.play();
      } catch (error) {
        onError?.(error as Error);
      }
    }
  }, [autoPlay, onError]);

  // Load audio from Blob
  const loadBlob = useCallback(async (blob: Blob) => {
    const url = URL.createObjectURL(blob);
    await loadAudio(url);

    // Cleanup URL when audio ends or changes
    const cleanup = () => {
      URL.revokeObjectURL(url);
      audioRef.current?.removeEventListener('ended', cleanup);
    };
    audioRef.current?.addEventListener('ended', cleanup);
  }, [loadAudio]);

  // Load audio from base64
  const loadBase64 = useCallback(async (base64: string, mimeType = 'audio/mp3') => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: mimeType });
    await loadBlob(blob);
  }, [loadBlob]);

  // Play
  const play = useCallback(async () => {
    if (!audioRef.current) return;

    try {
      await audioRef.current.play();
    } catch (error) {
      onError?.(error as Error);
    }
  }, [onError]);

  // Pause
  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  // Stop
  const stop = useCallback(() => {
    if (!audioRef.current) return;

    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    setCurrentTime(0);
    setState('idle');
    stopProgressTracking();
  }, [stopProgressTracking]);

  // Seek
  const seek = useCallback((position: number) => {
    if (!audioRef.current || !duration) return;

    const clampedPosition = Math.max(0, Math.min(1, position));
    audioRef.current.currentTime = clampedPosition * duration;
    setCurrentTime(audioRef.current.currentTime);
  }, [duration]);

  // Set volume
  const setVolume = useCallback((newVolume: number) => {
    if (!audioRef.current) return;

    const clampedVolume = Math.max(0, Math.min(1, newVolume));
    audioRef.current.volume = clampedVolume;
    setVolumeState(clampedVolume);
  }, []);

  // Set playback rate
  const setPlaybackRate = useCallback((rate: number) => {
    if (!audioRef.current) return;

    const clampedRate = Math.max(0.5, Math.min(2, rate));
    audioRef.current.playbackRate = clampedRate;
  }, []);

  // Queue audio
  const queue = useCallback((url: string) => {
    queueRef.current.push(url);

    // If nothing is playing, start playback
    if (state === 'idle' || state === 'ended') {
      playNext();
    }
  }, [state, playNext]);

  // Clear queue
  const clearQueue = useCallback(() => {
    queueRef.current = [];
  }, []);

  return {
    state,
    isPlaying: state === 'playing',
    currentTime,
    duration,
    volume,
    loadAudio,
    loadBlob,
    loadBase64,
    play,
    pause,
    stop,
    seek,
    setVolume,
    setPlaybackRate,
    queue,
    clearQueue,
  };
}
