import { configureStore } from '@reduxjs/toolkit';
import { combineReducers } from 'redux';
import teamsReducer from './slices/teamsSlice';
import playersReducer from './slices/playersSlice';
import shotsReducer from './slices/shotsSlice';
import uiReducer from './slices/uiSlice';

// Combine all reducers
const rootReducer = combineReducers({
  teams: teamsReducer,
  players: playersReducer,
  shots: shotsReducer,
  ui: uiReducer,
});

// Configure the Redux store
const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

// Types for state and dispatch
export type RootState = ReturnType<typeof rootReducer>;
export type AppDispatch = typeof store.dispatch;

export default store;