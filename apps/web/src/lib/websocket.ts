const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8100';

export type MessageType = 'message' | 'audio_chunk' | 'control';
export type ResponseType = 'ai_response' | 'transcription' | 'status' | 'error' | 'time_warning' | 'coverage_update' | 'followup_suggestions';

export interface WSMessage {
  type: MessageType;
  payload: {
    content?: string;
    audio?: string;
    action?: 'pause' | 'resume' | 'end';
  };
}

export interface WSResponse {
  type: ResponseType;
  payload: {
    content?: string;
    audio?: string;
    isPartial?: boolean;
    isFinal?: boolean;
    speaker?: string;
    text?: string;
    timestamp?: number;
    status?: string;
    message?: string;
    summary?: Record<string, unknown>;
    duration_minutes?: number;
    level?: string;
    remaining_seconds?: number;
    overall_percentage?: number;
    questions?: Array<{ question: string; status: string; percentage: number }>;
    suggest_end?: boolean;
    coverage?: Record<string, unknown>;
    carry_over?: Record<string, unknown>;
    quality?: Record<string, unknown>;
    suggestions?: string[];
  };
}

export class InterviewWebSocket {
  private ws: WebSocket | null = null;
  private interviewId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;

  public onMessage: ((response: WSResponse) => void) | null = null;
  public onOpen: (() => void) | null = null;
  public onClose: (() => void) | null = null;
  public onError: ((error: Event) => void) | null = null;

  constructor(interviewId: string) {
    this.interviewId = interviewId;
  }

  connect(): void {
    if (this.disposed) return;

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const params = token ? `?token=${encodeURIComponent(token)}` : '';
    const url = `${WS_URL}/api/v1/interviews/${this.interviewId}/stream${params}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.onOpen?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const response: WSResponse = JSON.parse(event.data);
        this.onMessage?.(response);
      } catch {
        // Silently ignore unparseable messages
      }
    };

    this.ws.onclose = () => {
      this.onClose?.();
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      this.onError?.(error);
    };
  }

  private attemptReconnect(): void {
    if (this.disposed || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  sendMessage(content: string): void {
    this.send({
      type: 'message',
      payload: { content },
    });
  }

  sendControl(action: 'pause' | 'resume' | 'end'): void {
    this.send({
      type: 'control',
      payload: { action },
    });
  }

  sendAudio(audioBase64: string, format: string = 'webm'): void {
    this.send({
      type: 'audio_chunk',
      payload: { audio: audioBase64 },
    });
  }

  disconnect(): void {
    this.disposed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export function createInterviewWebSocket(interviewId: string): InterviewWebSocket {
  return new InterviewWebSocket(interviewId);
}
