import axios from 'axios';
import type {
  DownloadOptions,
  ApiResponse,
  DownloadResponse,
  ProgressUpdate,
} from '../types/spotdl';

// Base API URL - this will connect to the backend (Python FastAPI or spotdl web server)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8800/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service
export const spotdlApi = {
  // Start a download
  download: async (options: DownloadOptions): Promise<ApiResponse<DownloadResponse>> => {
    try {
      const response = await api.post('/download', options);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Download failed',
      };
    }
  },

  // Get download status
  getStatus: async (downloadId: string): Promise<ApiResponse<ProgressUpdate>> => {
    try {
      const response = await api.get(`/download/${downloadId}/status`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get status',
      };
    }
  },

  // Cancel a download
  cancelDownload: async (downloadId: string): Promise<ApiResponse> => {
    try {
      await api.delete(`/download/${downloadId}`);
      return {
        success: true,
        message: 'Download cancelled',
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to cancel',
      };
    }
  },

  // Get available audio providers
  getAudioProviders: async (): Promise<ApiResponse<string[]>> => {
    try {
      const response = await api.get('/providers/audio');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      // Return default providers if API fails
      return {
        success: true,
        data: ['youtube', 'youtube-music', 'slider-kz', 'soundcloud', 'bandcamp', 'piped'],
      };
    }
  },

  // Get available lyrics providers
  getLyricsProviders: async (): Promise<ApiResponse<string[]>> => {
    try {
      const response = await api.get('/providers/lyrics');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      // Return default providers if API fails
      return {
        success: true,
        data: ['genius', 'musixmatch', 'azlyrics', 'synced'],
      };
    }
  },

  // Validate Spotify URL/query
  validateQuery: async (query: string): Promise<ApiResponse<{ valid: boolean; type?: string }>> => {
    try {
      const response = await api.post('/validate', { query });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Validation failed',
      };
    }
  },

  // Health check
  healthCheck: async (): Promise<boolean> => {
    try {
      const response = await api.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  },
};

export default api;
