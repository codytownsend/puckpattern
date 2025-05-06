import { createSlice } from '@reduxjs/toolkit';

// Initial state
const initialState = {
  teams: [],
  selectedTeam: null,
  isLoading: false,
  error: null
};

// Create slice
const teamsSlice = createSlice({
  name: 'teams',
  initialState,
  reducers: {
    // Add your reducers here
  }
});

export default teamsSlice.reducer;