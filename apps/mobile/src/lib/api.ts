/**
 * API client for the mobile app.
 */

import * as SecureStore from 'expo-secure-store';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8100';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async getAuthToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync('access_token');
    } catch {
      return null;
    }
  }

  async setAuthToken(token: string): Promise<void> {
    await SecureStore.setItemAsync('access_token', token);
  }

  async clearAuthToken(): Promise<void> {
    await SecureStore.deleteItemAsync('access_token');
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;

    const token = await this.getAuthToken();

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth endpoints
  auth = {
    login: async (email: string, password: string) => {
      const response = await this.request<{ access_token: string; refresh_token: string }>(
        '/api/v1/auth/login',
        {
          method: 'POST',
          body: { email, password },
        }
      );
      await this.setAuthToken(response.access_token);
      return response;
    },

    logout: async () => {
      await this.clearAuthToken();
    },

    me: () => this.request<{ id: string; email: string; name: string }>('/api/v1/auth/me'),
  };

  // Projects
  projects = {
    list: () => this.request<unknown[]>('/api/v1/projects'),
    get: (id: string) => this.request<unknown>(`/api/v1/projects/${id}`),
  };

  // Tasks
  tasks = {
    list: (params?: { project_id?: string; status?: string }) => {
      const query = new URLSearchParams(params as Record<string, string>).toString();
      return this.request<unknown[]>(`/api/v1/tasks${query ? `?${query}` : ''}`);
    },
    get: (id: string) => this.request<unknown>(`/api/v1/tasks/${id}`),
  };

  // Interviews
  interviews = {
    list: (params?: { task_id?: string; status?: string }) => {
      const query = new URLSearchParams(params as Record<string, string>).toString();
      return this.request<unknown[]>(`/api/v1/interviews${query ? `?${query}` : ''}`);
    },
    get: (id: string) => this.request<unknown>(`/api/v1/interviews/${id}`),
    create: (data: { task_id: string; language?: string }) =>
      this.request<unknown>('/api/v1/interviews', { method: 'POST', body: data }),
    start: (id: string) =>
      this.request<unknown>(`/api/v1/interviews/${id}/start`, { method: 'POST' }),
    complete: (id: string) =>
      this.request<unknown>(`/api/v1/interviews/${id}/complete`, { method: 'POST' }),
    getTranscript: (id: string) =>
      this.request<unknown[]>(`/api/v1/interviews/${id}/transcript`),
  };

  // Knowledge
  knowledge = {
    search: (query: string, limit = 10) =>
      this.request<unknown[]>('/api/v1/knowledge/search', {
        method: 'POST',
        body: { query, limit },
      }),
  };

  // Reports
  reports = {
    list: () => this.request<unknown[]>('/api/v1/reports'),
    get: (id: string) => this.request<unknown>(`/api/v1/reports/${id}`),
    generate: (data: { interview_id: string; report_type: string }) =>
      this.request<unknown>('/api/v1/reports/generate', { method: 'POST', body: data }),
  };
}

export const api = new ApiClient(API_URL);
export default api;
