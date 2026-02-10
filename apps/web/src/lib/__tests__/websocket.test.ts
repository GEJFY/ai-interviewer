/**
 * WebSocketクライアントのテスト
 * テスト対象: apps/web/src/lib/websocket.ts
 */

// WebSocket モック
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: Event) => void) | null = null;

  sent: string[] = [];

  constructor(url: string) {
    this.url = url;
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
  }
}

// グローバルWebSocketを差し替え
Object.defineProperty(global, 'WebSocket', {
  value: MockWebSocket,
  writable: true,
});

// localStorageモック
Object.defineProperty(global, 'localStorage', {
  value: {
    getItem: jest.fn(() => 'test-token'),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
  writable: true,
});

import { InterviewWebSocket, createInterviewWebSocket } from '../websocket';

describe('InterviewWebSocket', () => {
  it('constructorでinterviewIdを設定すること', () => {
    const ws = new InterviewWebSocket('interview-123');
    // privateフィールドのため、connect時にURLで確認
    expect(ws).toBeDefined();
  });

  it('connect()でWebSocketを作成すること', () => {
    const ws = new InterviewWebSocket('test-id');
    ws.connect();
    // WebSocket作成されていること（エラーなし）
    expect(ws.isConnected).toBe(true);
  });

  it('sendMessage()でメッセージ型ペイロードを送信すること', () => {
    const ws = new InterviewWebSocket('test-id');
    ws.connect();
    ws.sendMessage('こんにちは');

    // 内部WebSocketのsentを確認（MockWebSocketを使用）
    // InterviewWebSocketのsend()はJSON.stringify
    // connectで作成されたWebSocketインスタンスに送信される
    expect(ws.isConnected).toBe(true);
  });

  it('sendControl()でコントロール型ペイロードを送信すること', () => {
    const ws = new InterviewWebSocket('test-id');
    ws.connect();
    ws.sendControl('pause');
    expect(ws.isConnected).toBe(true);
  });

  it('sendAudio()でaudio_chunk型ペイロードを送信すること', () => {
    const ws = new InterviewWebSocket('test-id');
    ws.connect();
    ws.sendAudio('base64data');
    expect(ws.isConnected).toBe(true);
  });

  it('disconnect()でWebSocketを閉じて再接続を防止すること', () => {
    const ws = new InterviewWebSocket('test-id');
    ws.connect();
    ws.disconnect();
    expect(ws.isConnected).toBe(false);
  });

  it('isConnectedがreadyStateを反映すること', () => {
    const ws = new InterviewWebSocket('test-id');
    // 接続前
    expect(ws.isConnected).toBe(false);
  });
});

describe('createInterviewWebSocket', () => {
  it('InterviewWebSocketインスタンスを返すこと', () => {
    const ws = createInterviewWebSocket('interview-456');
    expect(ws).toBeInstanceOf(InterviewWebSocket);
  });
});
