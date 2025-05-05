import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ShotsFilter, Shot, ShotHeatmap } from '../store/slices/shotsSlice';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to handle authentication
api.interceptors.request.use(
  (config) => {
    // Add auth token if it exists
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Add global error handling logic here
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Shots API

export const fetchShots = async (
  filters: ShotsFilter = {}
): Promise<Shot[]> => {
  // Convert filters to query string
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, value.toString());
    }
  });
  
  const response = await api.get(`/shots?${params.toString()}`);
  return response.data;
};

export const fetchShotHeatmap = async (
  filters: ShotsFilter & { normalize?: boolean } = {}
): Promise<ShotHeatmap> => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, value.toString());
    }
  });
  
  const response = await api.get(`/shots/heatmap?${params.toString()}`);
  return response.data;
};

export const fetchPlayerDangerousZones = async (
  player_id: string,
  season?: string
): Promise<any> => {
  const params = new URLSearchParams();
  if (season) {
    params.append('season', season);
  }
  
  const response = await api.get(`/shots/dangerous-zones/${player_id}?${params.toString()}`);
  return response.data;
};

export const fetchTeamComparison = async (
  team_id1: string,
  team_id2: string,
  season?: string
): Promise<any> => {
  const params = new URLSearchParams();
  if (season) {
    params.append('season', season);
  }
  
  params.append('team_id1', team_id1);
  params.append('team_id2', team_id2);
  
  const response = await api.get(`/shots/team-comparison?${params.toString()}`);
  return response.data;
};

export const fetchXGBreakdown = async (
  player_id: string,
  season?: string
): Promise<any> => {
  const params = new URLSearchParams();
  if (season) {
    params.append('season', season);
  }
  
  const response = await api.get(`/shots/xg-breakdown?player_id=${player_id}&${params.toString()}`);
  return response.data;
};

// Teams API

export const fetchTeams = async (): Promise<any[]> => {
  const response = await api.get('/teams');
  return response.data;
};

export const fetchTeamById = async (id: string): Promise<any> => {
  const response = await api.get(`/teams/${id}`);
  return response.data;
};

// Players API

export const fetchPlayers = async (filters: Record<string, any> = {}): Promise<any[]> => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, value.toString());
    }
  });
  
  const response = await api.get(`/players?${params.toString()}`);
  return response.data;
};

export const fetchPlayerById = async (id: string): Promise<any> => {
  const response = await api.get(`/players/${id}`);
  return response.data;
};

// Games API

export const fetchGames = async (filters: Record<string, any> = {}): Promise<any[]> => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, value.toString());
    }
  });
  
  const response = await api.get(`/games?${params.toString()}`);
  return response.data;
};

export const fetchGameById = async (id: string): Promise<any> => {
  const response = await api.get(`/games/${id}`);
  return response.data;
};

// Generic request handler
export const request = async <T = any>(
  config: AxiosRequestConfig
): Promise<T> => {
  const response: AxiosResponse<T> = await api(config);
  return response.data;
};

export default api;