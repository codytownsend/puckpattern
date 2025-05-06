import { createSlice } from '@reduxjs/toolkit';

// Initial state
const initialState = {
  players: [],
  selectedPlayer: null,
  isLoading: false,
  error: null
};

// Create slice
const playersSlice = createSlice({
  name: 'players',
  initialState,
  reducers: {
    // Add your reducers here
  }
});

export default playersSlice.reducer;