const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export type MessageType = 'message' | 'audio_chunk' | 'control';
export type ResponseType = 'ai_response' | 'transcription' | 'status' | 'error';

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
  };
}

export class InterviewWebSocket {
  private ws: WebSocket | null = null;
  private interviewId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  public onMessage: ((response: WSResponse) => void) | null = null;
  public onOpen: (() => void) | null = null;
  public onClose: (() => void) | null = null;
  public onError: ((error: Event) => void) | null = null;

  constructor(interviewId: string) {
    this.interviewId = interviewId;
  }

  connect(): void {
    const token = localStorage.getItem('access_token');
    const url = `${WS_URL}/api/v1/interviews/${this.interviewId}/stream`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.onOpen?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const response: WSResponse = JSON.parse(event.data);
        this.onMessage?.(response);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
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
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      setTimeout(() => this.connect(), delay);
    }
  }

  send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
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
    this.maxReconnectAttempts = 0; // Prevent reconnection
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
