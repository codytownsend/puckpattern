import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '..';

// Theme types
export type ThemeMode = 'light' | 'dark';

// Notification types
export interface Notification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

// UI State interface
export interface UIState {
  sidebarOpen: boolean;
  themeMode: ThemeMode;
  notifications: Notification[];
  currentModule: string | null;
  isLoading: {
    [key: string]: boolean;
  };
  visualizationOptions: {
    showLabels: boolean;
    normalizeData: boolean;
    colorScheme: string;
    gridSize: number;
  };
}

// Initial state
const initialState: UIState = {
  sidebarOpen: true,
  themeMode: 'light',
  notifications: [],
  currentModule: null,
  isLoading: {},
  visualizationOptions: {
    showLabels: true,
    normalizeData: true,
    colorScheme: 'blues',
    gridSize: 10
  }
};

// UI Slice
const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setThemeMode: (state, action: PayloadAction<ThemeMode>) => {
      state.themeMode = action.payload;
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id'>>) => {
      const id = Date.now().toString();
      state.notifications.push({
        ...action.payload,
        id
      });
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      );
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setCurrentModule: (state, action: PayloadAction<string | null>) => {
      state.currentModule = action.payload;
    },
    setIsLoading: (state, action: PayloadAction<{ key: string; isLoading: boolean }>) => {
      state.isLoading[action.payload.key] = action.payload.isLoading;
    },
    setVisualizationOption: (
      state,
      action: PayloadAction<{
        option: keyof UIState['visualizationOptions'];
        value: any;
      }>
    ) => {
      const { option, value } = action.payload;
      state.visualizationOptions[option] = value;
    },
    resetVisualizationOptions: (state) => {
      state.visualizationOptions = initialState.visualizationOptions;
    }
  }
});

// Actions
export const {
  toggleSidebar,
  setSidebarOpen,
  setThemeMode,
  addNotification,
  removeNotification,
  clearNotifications,
  setCurrentModule,
  setIsLoading,
  setVisualizationOption,
  resetVisualizationOptions
} = uiSlice.actions;

// Selectors
export const selectSidebarOpen = (state: RootState) => state.ui.sidebarOpen;
export const selectThemeMode = (state: RootState) => state.ui.themeMode;
export const selectNotifications = (state: RootState) => state.ui.notifications;
export const selectCurrentModule = (state: RootState) => state.ui.currentModule;
export const selectIsLoading = (state: RootState, key: string) => !!state.ui.isLoading[key];
export const selectVisualizationOptions = (state: RootState) => state.ui.visualizationOptions;

export default uiSlice.reducer;