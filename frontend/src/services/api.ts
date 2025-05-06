import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ShotsFilter, Shot, ShotHeatmap } from '../store/slices/shotsSlice';

// Create axios instance with default config
const api = axios.create({
  // Updated to ensure correct API URL configuration
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

// Enhanced response interceptor with better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Add global error handling logic here
    console.error('API Error:', error);
    
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Shots API with improved error handling

export const fetchShots = async (
  filters: ShotsFilter = {}
): Promise<Shot[]> => {
  try {
    // Convert filters to query string
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    
    console.log('Fetching shots with params:', params.toString());
    const response = await api.get(`/shots?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching shots:', error);
    // Return empty array instead of throwing
    return [];
  }
};

export const fetchShotHeatmap = async (
  filters: ShotsFilter & { normalize?: boolean } = {}
): Promise<ShotHeatmap> => {
  try {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    
    console.log('Fetching shot heatmap with params:', params.toString());
    const response = await api.get(`/shots/heatmap?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching shot heatmap:', error);
    throw error; // Re-throw to be handled by Redux
  }
};

export const fetchPlayerDangerousZones = async (
  player_id: string,
  season?: string
): Promise<any> => {
  try {
    const params = new URLSearchParams();
    if (season) {
      params.append('season', season);
    }
    
    const response = await api.get(`/shots/dangerous-zones/${player_id}?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching player dangerous zones:', error);
    throw error;
  }
};

export const fetchTeamComparison = async (
  team_id1: string,
  team_id2: string,
  season?: string
): Promise<any> => {
  try {
    const params = new URLSearchParams();
    if (season) {
      params.append('season', season);
    }
    
    params.append('team_id1', team_id1);
    params.append('team_id2', team_id2);
    
    const response = await api.get(`/shots/team-comparison?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching team comparison:', error);
    throw error;
  }
};

export const fetchXGBreakdown = async (
  player_id: string,
  season?: string
): Promise<any> => {
  try {
    const params = new URLSearchParams();
    if (season) {
      params.append('season', season);
    }
    
    const response = await api.get(`/shots/xg-breakdown?player_id=${player_id}&${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching XG breakdown:', error);
    throw error;
  }
};

// Teams API

export const fetchTeams = async (): Promise<any[]> => {
  try {
    const response = await api.get('/teams');
    return response.data;
  } catch (error) {
    console.error('Error fetching teams:', error);
    return [];
  }
};

export const fetchTeamById = async (id: string): Promise<any> => {
  try {
    const response = await api.get(`/teams/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching team:', error);
    throw error;
  }
};

// Players API

export const fetchPlayers = async (filters: Record<string, any> = {}): Promise<any[]> => {
  try {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    
    const response = await api.get(`/players?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching players:', error);
    return [];
  }
};

export const fetchPlayerById = async (id: string): Promise<any> => {
  try {
    const response = await api.get(`/players/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching player:', error);
    throw error;
  }
};

// Games API

export const fetchGames = async (filters: Record<string, any> = {}): Promise<any[]> => {
  try {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    
    const response = await api.get(`/games?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching games:', error);
    return [];
  }
};

export const fetchGameById = async (id: string): Promise<any> => {
  try {
    const response = await api.get(`/games/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching game:', error);
    throw error;
  }
};

// Generic request handler
export const request = async <T = any>(
  config: AxiosRequestConfig
): Promise<T> => {
  try {
    const response: AxiosResponse<T> = await api(config);
    return response.data;
  } catch (error) {
    console.error('Error in generic request:', error);
    throw error;
  }
};

export default api;