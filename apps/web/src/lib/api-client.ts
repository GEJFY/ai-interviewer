import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          // Retry original request
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return apiClient.request(error.config);
          }
        } catch {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// API functions
export const api = {
  // Auth
  auth: {
    login: async (email: string, password: string) => {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      const response = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      return response.data;
    },
    register: async (data: { email: string; name: string; password: string }) => {
      const response = await apiClient.post('/auth/register', data);
      return response.data;
    },
    me: async () => {
      const response = await apiClient.get('/auth/me');
      return response.data;
    },
  },

  // Projects
  projects: {
    list: async (params?: { page?: number; pageSize?: number; status?: string }) => {
      const response = await apiClient.get('/projects', { params });
      return response.data;
    },
    get: async (id: string) => {
      const response = await apiClient.get(`/projects/${id}`);
      return response.data;
    },
    create: async (data: { name: string; description?: string; clientName?: string }) => {
      const response = await apiClient.post('/projects', data);
      return response.data;
    },
    update: async (id: string, data: Partial<{ name: string; description: string; status: string }>) => {
      const response = await apiClient.put(`/projects/${id}`, data);
      return response.data;
    },
    delete: async (id: string) => {
      await apiClient.delete(`/projects/${id}`);
    },
  },

  // Tasks
  tasks: {
    list: async (params?: { projectId?: string; page?: number; pageSize?: number; status?: string }) => {
      const response = await apiClient.get('/tasks', { params });
      return response.data;
    },
    get: async (id: string) => {
      const response = await apiClient.get(`/tasks/${id}`);
      return response.data;
    },
    create: async (data: {
      name: string;
      projectId: string;
      useCaseType: string;
      templateId?: string;
      targetCount?: number;
    }) => {
      const response = await apiClient.post('/tasks', data);
      return response.data;
    },
  },

  // Interviews
  interviews: {
    list: async (params?: { taskId?: string; page?: number; pageSize?: number; status?: string }) => {
      const response = await apiClient.get('/interviews', { params });
      return response.data;
    },
    get: async (id: string) => {
      const response = await apiClient.get(`/interviews/${id}`);
      return response.data;
    },
    create: async (data: { taskId: string; intervieweeId?: string; language?: string }) => {
      const response = await apiClient.post('/interviews', data);
      return response.data;
    },
    start: async (id: string) => {
      const response = await apiClient.post(`/interviews/${id}/start`, {});
      return response.data;
    },
    complete: async (id: string, data?: { summary?: string }) => {
      const response = await apiClient.post(`/interviews/${id}/complete`, data || {});
      return response.data;
    },
    getTranscript: async (id: string) => {
      const response = await apiClient.get(`/interviews/${id}/transcript`);
      return response.data;
    },
  },

  // Templates
  templates: {
    list: async (params?: { useCaseType?: string; publishedOnly?: boolean }) => {
      const response = await apiClient.get('/templates', { params });
      return response.data;
    },
    get: async (id: string) => {
      const response = await apiClient.get(`/templates/${id}`);
      return response.data;
    },
    create: async (data: {
      name: string;
      useCaseType: string;
      description?: string;
      questions: Array<{ question: string; order: number; followUps?: string[]; required?: boolean }>;
    }) => {
      const response = await apiClient.post('/templates', data);
      return response.data;
    },
    update: async (
      id: string,
      data: {
        name?: string;
        description?: string;
        questions?: Array<{ question: string; order: number; followUps?: string[]; required?: boolean }>;
      }
    ) => {
      const response = await apiClient.put(`/templates/${id}`, data);
      return response.data;
    },
    delete: async (id: string) => {
      await apiClient.delete(`/templates/${id}`);
    },
    clone: async (id: string, data?: { name?: string }) => {
      const response = await apiClient.post(`/templates/${id}/clone`, data || {});
      return response.data;
    },
    publish: async (id: string) => {
      const response = await apiClient.post(`/templates/${id}/publish`, {});
      return response.data;
    },
  },

  // Reports
  reports: {
    list: async (params?: { interviewId?: string; taskId?: string; reportType?: string }) => {
      const response = await apiClient.get('/reports', { params });
      return response.data;
    },
    generate: async (data: { reportType: string; interviewId?: string; taskId?: string }) => {
      const response = await apiClient.post('/reports/generate', data);
      return response.data;
    },
    export: async (id: string, format: string = 'json') => {
      const response = await apiClient.get(`/reports/${id}/export`, {
        params: { format },
        responseType: 'blob',
      });
      return response.data;
    },
  },
};

export default api;
