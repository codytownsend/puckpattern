import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '..';
import * as api from '../../services/api';
import { mockHeatmapData } from '../../utils/mockData';

// Types
export interface Shot {
  id: number;
  shot_type: string;
  x_coordinate: number;
  y_coordinate: number;
  period: number;
  time_elapsed: number;
  distance?: number;
  angle?: number;
  goal: boolean;
  xg?: number;
  shooter: {
    id: number;
    name: string;
    team_id: number;
  };
  team: {
    id: number;
    name: string;
    abbreviation: string;
  };
  game: {
    id: number;
    game_id: string;
    date: string;
  };
  goalie?: {
    id: number;
    name: string;
  };
  primary_assist?: {
    id: number;
    name: string;
  };
  secondary_assist?: {
    id: number;
    name: string;
  };
}

export interface HeatmapPoint {
  x: number;
  y: number;
  value: number;
}

export interface ShotHeatmap {
  points: HeatmapPoint[];
  max_value: number;
  total_shots: number;
  total_goals: number;
  average_xg: number;
  metadata: {
    filters: any;
    grid_size: number;
  };
}

export interface ShotsFilter {
  game_id?: string;
  player_id?: string;
  team_id?: string;
  shot_type?: string;
  period?: number;
  is_goal?: boolean;
  goal_only?: boolean;
  min_xg?: number;
  max_xg?: number;
  season?: string;
  normalize?: boolean;
}

export interface ShotsState {
  shots: Shot[];
  heatmap: ShotHeatmap | null;
  filteredShots: Shot[];
  playerDangerousZones: any | null;
  teamComparison: any | null;
  xgBreakdown: any | null;
  isLoading: boolean;
  error: string | null;
  filters: ShotsFilter;
}

// Initial state
const initialState: ShotsState = {
  shots: [],
  heatmap: null,
  filteredShots: [],
  playerDangerousZones: null,
  teamComparison: null,
  xgBreakdown: null,
  isLoading: false,
  error: null,
  filters: {}
};

// Async thunks
export const fetchShots = createAsyncThunk(
  'shots/fetchShots',
  async (filters: ShotsFilter, { rejectWithValue }) => {
    try {
      // Use the API service to fetch data
      const data = await api.fetchShots(filters);
      return data;
    } catch (error: any) {
      console.error('Error fetching shots:', error);
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const fetchShotHeatmap = createAsyncThunk(
  'shots/fetchShotHeatmap',
  async (filters: ShotsFilter & { normalize?: boolean }, { rejectWithValue }) => {
    try {
      console.log('Fetching shot heatmap with filters:', filters);
      
      // Use the API service to fetch data
      const data = await api.fetchShotHeatmap(filters);
      return data;
    } catch (error: any) {
      console.error('Error fetching shot heatmap:', error);
      
      // If in development environment, use mock data as fallback
      if (process.env.NODE_ENV === 'development') {
        console.log('Using mock data as fallback');
        return mockHeatmapData;
      }
      
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const fetchPlayerDangerousZones = createAsyncThunk(
  'shots/fetchPlayerDangerousZones',
  async ({ player_id, season }: { player_id: string, season?: string }, { rejectWithValue }) => {
    try {
      // Use the API service to fetch data
      const data = await api.fetchPlayerDangerousZones(player_id, season);
      return data;
    } catch (error: any) {
      console.error('Error fetching player dangerous zones:', error);
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const fetchTeamComparison = createAsyncThunk(
  'shots/fetchTeamComparison',
  async ({ team_id1, team_id2, season }: { team_id1: string, team_id2: string, season?: string }, { rejectWithValue }) => {
    try {
      // Use the API service to fetch data
      const data = await api.fetchTeamComparison(team_id1, team_id2, season);
      return data;
    } catch (error: any) {
      console.error('Error fetching team comparison:', error);
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

export const fetchXGBreakdown = createAsyncThunk(
  'shots/fetchXGBreakdown',
  async ({ player_id, season }: { player_id: string, season?: string }, { rejectWithValue }) => {
    try {
      // Use the API service to fetch data
      const data = await api.fetchXGBreakdown(player_id, season);
      return data;
    } catch (error: any) {
      console.error('Error fetching XG breakdown:', error);
      return rejectWithValue(error.response?.data?.message || error.message);
    }
  }
);

// Slice
const shotsSlice = createSlice({
  name: 'shots',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ShotsFilter>) => {
      state.filters = action.payload;
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    filterShots: (state, action: PayloadAction<ShotsFilter>) => {
      const filters = action.payload;
      state.filteredShots = state.shots.filter(shot => {
        // Check each filter condition
        if (filters.game_id && shot.game.game_id !== filters.game_id) return false;
        if (filters.player_id && shot.shooter.id.toString() !== filters.player_id) return false;
        if (filters.team_id && shot.team.id.toString() !== filters.team_id) return false;
        if (filters.shot_type && shot.shot_type !== filters.shot_type) return false;
        if (filters.period && shot.period !== filters.period) return false;
        if (filters.is_goal !== undefined && shot.goal !== filters.is_goal) return false;
        if (filters.goal_only && !shot.goal) return false;
        if (filters.min_xg !== undefined && shot.xg !== undefined && shot.xg < filters.min_xg) return false;
        if (filters.max_xg !== undefined && shot.xg !== undefined && shot.xg > filters.max_xg) return false;
        
        return true;
      });
    },
    // Action to set mock data (for development/testing)
    setMockHeatmapData: (state) => {
      state.heatmap = mockHeatmapData;
      state.error = null;
      state.isLoading = false;
    },
    clearHeatmap: (state) => {
      state.heatmap = null;
    },
    clearTeamComparison: (state) => {
      state.teamComparison = null;
    },
    clearXGBreakdown: (state) => {
      state.xgBreakdown = null;
    },
    clearPlayerDangerousZones: (state) => {
      state.playerDangerousZones = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch shots
      .addCase(fetchShots.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchShots.fulfilled, (state, action) => {
        state.isLoading = false;
        state.shots = action.payload;
        state.filteredShots = action.payload;
      })
      .addCase(fetchShots.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Fetch shot heatmap
      .addCase(fetchShotHeatmap.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchShotHeatmap.fulfilled, (state, action) => {
        state.isLoading = false;
        state.heatmap = action.payload;
      })
      .addCase(fetchShotHeatmap.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        
        // If mock data is provided as a fallback in development
        if (process.env.NODE_ENV === 'development' && action.payload === mockHeatmapData) {
          state.heatmap = mockHeatmapData;
          state.error = 'Using mock data due to API error. This is fine in development.';
        }
      })
      
      // Fetch player dangerous zones
      .addCase(fetchPlayerDangerousZones.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPlayerDangerousZones.fulfilled, (state, action) => {
        state.isLoading = false;
        state.playerDangerousZones = action.payload;
      })
      .addCase(fetchPlayerDangerousZones.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Fetch team comparison
      .addCase(fetchTeamComparison.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTeamComparison.fulfilled, (state, action) => {
        state.isLoading = false;
        state.teamComparison = action.payload;
      })
      .addCase(fetchTeamComparison.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Fetch XG breakdown
      .addCase(fetchXGBreakdown.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchXGBreakdown.fulfilled, (state, action) => {
        state.isLoading = false;
        state.xgBreakdown = action.payload;
      })
      .addCase(fetchXGBreakdown.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  }
});

// Actions
export const { 
  setFilters, 
  clearFilters, 
  filterShots, 
  clearHeatmap, 
  clearTeamComparison, 
  clearXGBreakdown, 
  clearPlayerDangerousZones,
  setMockHeatmapData
} = shotsSlice.actions;

// Selectors
export const selectShots = (state: RootState) => state.shots.filteredShots;
export const selectShotHeatmap = (state: RootState) => state.shots.heatmap;
export const selectPlayerDangerousZones = (state: RootState) => state.shots.playerDangerousZones;
export const selectTeamComparison = (state: RootState) => state.shots.teamComparison;
export const selectXGBreakdown = (state: RootState) => state.shots.xgBreakdown;
export const selectShotsLoading = (state: RootState) => state.shots.isLoading;
export const selectShotsError = (state: RootState) => state.shots.error;
export const selectShotsFilters = (state: RootState) => state.shots.filters;

export default shotsSlice.reducer;