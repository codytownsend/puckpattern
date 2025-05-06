import React, { useEffect, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Grid, 
  Typography, 
  Paper, 
  Box, 
  Card, 
  CardContent, 
  FormControl, 
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Button,
  Chip,
  Divider,
  Stack,
  Switch,
  FormControlLabel,
  IconButton,
  Tooltip,
  CircularProgress,
  useTheme,
  useMediaQuery
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import InfoIcon from '@mui/icons-material/Info';

import ShotHeatmap from '../components/visualizations/ShotHeatmap';
import { 
  fetchShotHeatmap, 
  selectShotHeatmap,
  selectShotsLoading,
  selectShotsError,
  setFilters,
  selectShotsFilters,
  HeatmapPoint
} from '../store/slices/shotsSlice';
import { setVisualizationOption, selectVisualizationOptions, VisualizationOptions } from '../store/slices/uiSlice';
import { AppDispatch } from '../store';

// Import mock data for development or when API fails
import { mockHeatmapData, mockTeams, mockPlayers } from '../utils/mockData';

const ShotMap: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Redux state
  const heatmapData = useSelector(selectShotHeatmap);
  const isLoading = useSelector(selectShotsLoading);
  const error = useSelector(selectShotsError);
  const visualizationOptions = useSelector(selectVisualizationOptions);
  
  // Local state management
  const [teams] = useState<any[]>(mockTeams);
  const [players] = useState<any[]>(mockPlayers);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [selectedPlayer, setSelectedPlayer] = useState<string>('');
  const [selectedSeason, setSelectedSeason] = useState<string>('2024-2025');
  const [selectedShotType, setSelectedShotType] = useState<string>('All');
  const [showGoalsOnly, setShowGoalsOnly] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Fixed data
  const seasons = ['2023-2024', '2024-2025'];
  const shotTypes = ['All', 'Wrist Shot', 'Slap Shot', 'Snap Shot', 'Backhand', 'Tip-In', 'Deflection'];
  
  // Memoize the handleApplyFilters function to avoid dependency issues in useEffect
  const handleApplyFilters = useCallback(() => {
    // Clear any previous error
    setErrorMessage(null);
    
    // Prepare filters
    const shotType = selectedShotType !== 'All' ? selectedShotType : undefined;
    
    const newFilters = {
      team_id: selectedTeam || undefined,
      player_id: selectedPlayer || undefined,
      season: selectedSeason,
      shot_type: shotType,
      goal_only: showGoalsOnly || undefined,
      normalize: visualizationOptions.normalizeData
    };
    
    // Update filters in store
    dispatch(setFilters(newFilters));
    
    // Fetch heatmap data
    dispatch(fetchShotHeatmap(newFilters))
      .unwrap()
      .catch(err => {
        console.error('Error fetching shot heatmap:', err);
        setErrorMessage(err.toString());
      });
  }, [
    dispatch, 
    selectedTeam, 
    selectedPlayer, 
    selectedSeason, 
    selectedShotType,
    showGoalsOnly,
    visualizationOptions.normalizeData
  ]);
  
  // Initialize by loading heatmap with default filters
  useEffect(() => {
    // Only fetch if we don't already have data and not currently loading
    if (!heatmapData && !isLoading) {
      console.log('Fetching initial heatmap data');
      handleApplyFilters();
    }
  }, [heatmapData, isLoading, handleApplyFilters]);
  
  // Effect to handle errors
  useEffect(() => {
    if (error) {
      console.error('Error in shots data fetch:', error);
      setErrorMessage(error);
      
      // If API fails, use mock data as fallback
      if (!heatmapData) {
        console.log('Using mock heatmap data as fallback');
      }
    } else {
      setErrorMessage(null);
    }
  }, [error, heatmapData]);
  
  const handleTeamChange = (event: SelectChangeEvent) => {
    setSelectedTeam(event.target.value);
    // Clear player selection if team changes
    setSelectedPlayer('');
  };
  
  const handlePlayerChange = (event: SelectChangeEvent) => {
    setSelectedPlayer(event.target.value);
    // Clear team selection if player is selected
    if (event.target.value) {
      setSelectedTeam('');
    }
  };
  
  const handleSeasonChange = (event: SelectChangeEvent) => {
    setSelectedSeason(event.target.value);
  };
  
  const handleShotTypeChange = (event: SelectChangeEvent) => {
    setSelectedShotType(event.target.value);
  };
  
  const handleGoalsOnlyChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setShowGoalsOnly(event.target.checked);
  };
  
  // Fixed typing by using a proper literal type for option
  const handleVisualizationOptionChange = (option: keyof VisualizationOptions, value: any) => {
    dispatch(setVisualizationOption({ option, value }));
  };
  
  const handleExportData = () => {
    if (!heatmapData) {
      console.warn('No data to export');
      return;
    }
    
    // Create CSV data
    const csvData = [
      ['x', 'y', 'value'],
      ...heatmapData.points.map((point: HeatmapPoint) => [point.x, point.y, point.value])
    ].map(row => row.join(',')).join('\n');
    
    // Create download link
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', 'shot_heatmap_data.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };
  
  const handleCompareTeams = () => {
    // This would open a comparison modal in a full implementation
    console.log('Compare teams functionality to be implemented');
  };
  
  // Reset all filters
  const handleResetFilters = () => {
    setSelectedTeam('');
    setSelectedPlayer('');
    setSelectedShotType('All');
    setShowGoalsOnly(false);
    
    // Reset visualization options to defaults
    dispatch(setVisualizationOption({ option: 'showLabels', value: true }));
    dispatch(setVisualizationOption({ option: 'normalizeData', value: true }));
    dispatch(setVisualizationOption({ option: 'colorScheme', value: 'blues' }));
    
    // Apply the reset filters
    handleApplyFilters();
  };
  
  // Filter players based on selected team
  const filteredPlayers = selectedTeam 
    ? players.filter(player => player.team_id === selectedTeam) 
    : players;
  
  // Determine if we should show mock data when API fails
  const displayData = heatmapData || (error && mockHeatmapData);
  
  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Shot & Chance Map
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Visualize and analyze shot locations, expected goals (xG), and scoring patterns.
        </Typography>
      </Box>
      
      <Grid container spacing={3}>
        {/* Filters Panel */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Filters
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box mb={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="season-label">Season</InputLabel>
                <Select
                  labelId="season-label"
                  id="season-select"
                  value={selectedSeason}
                  label="Season"
                  onChange={handleSeasonChange}
                >
                  {seasons.map((season) => (
                    <MenuItem key={season} value={season}>{season}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box mb={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="team-label">Team</InputLabel>
                <Select
                  labelId="team-label"
                  id="team-select"
                  value={selectedTeam}
                  label="Team"
                  onChange={handleTeamChange}
                  disabled={!!selectedPlayer}
                >
                  <MenuItem value="">All Teams</MenuItem>
                  {teams.map((team) => (
                    <MenuItem key={team.id} value={team.id}>{team.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box mb={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="player-label">Player</InputLabel>
                <Select
                  labelId="player-label"
                  id="player-select"
                  value={selectedPlayer}
                  label="Player"
                  onChange={handlePlayerChange}
                  disabled={!!selectedTeam}
                >
                  <MenuItem value="">All Players</MenuItem>
                  {filteredPlayers.map((player) => (
                    <MenuItem key={player.id} value={player.id}>{player.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box mb={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="shot-type-label">Shot Type</InputLabel>
                <Select
                  labelId="shot-type-label"
                  id="shot-type-select"
                  value={selectedShotType}
                  label="Shot Type"
                  onChange={handleShotTypeChange}
                >
                  {shotTypes.map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box mb={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={showGoalsOnly}
                    onChange={handleGoalsOnlyChange}
                  />
                }
                label="Goals Only"
              />
            </Box>
            
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
              Visualization Options
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box mb={2}>
              <FormControlLabel 
                control={
                  <Switch 
                    checked={visualizationOptions.showLabels} 
                    onChange={(e) => handleVisualizationOptionChange('showLabels', e.target.checked)}
                  />
                } 
                label="Show Labels" 
              />
            </Box>
            
            <Box mb={2}>
              <FormControlLabel 
                control={
                  <Switch 
                    checked={visualizationOptions.normalizeData} 
                    onChange={(e) => handleVisualizationOptionChange('normalizeData', e.target.checked)}
                  />
                } 
                label="Normalize Data" 
              />
            </Box>
            
            <Box mb={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="color-scheme-label">Color Scheme</InputLabel>
                <Select
                  labelId="color-scheme-label"
                  id="color-scheme-select"
                  value={visualizationOptions.colorScheme}
                  label="Color Scheme"
                  onChange={(e) => handleVisualizationOptionChange('colorScheme', e.target.value)}
                >
                  <MenuItem value="blues">Blues</MenuItem>
                  <MenuItem value="reds">Reds</MenuItem>
                  <MenuItem value="greens">Greens</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
            </Box>
            
            <Stack direction="row" spacing={2}>
              <Button 
                variant="contained" 
                fullWidth 
                color="primary" 
                onClick={handleApplyFilters}
                disabled={isLoading}
              >
                {isLoading ? <CircularProgress size={24} color="inherit" /> : "Apply"}
              </Button>
              
              <Button 
                variant="outlined" 
                color="secondary" 
                onClick={handleResetFilters}
                disabled={isLoading}
              >
                Reset
              </Button>
            </Stack>
          </Paper>
        </Grid>
        
        {/* Main Content */}
        <Grid item xs={12} md={9}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Shot Heatmap
                {selectedTeam && teams.find(t => t.id === selectedTeam) && (
                  <Chip 
                    label={teams.find(t => t.id === selectedTeam)?.name} 
                    size="small" 
                    sx={{ ml: 2 }}
                  />
                )}
                {selectedPlayer && players.find(p => p.id === selectedPlayer) && (
                  <Chip 
                    label={players.find(p => p.id === selectedPlayer)?.name} 
                    size="small" 
                    sx={{ ml: 2 }}
                  />
                )}
              </Typography>
              
              <Box>
                <Tooltip title="Refresh Data">
                  <IconButton onClick={handleApplyFilters} disabled={isLoading}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export Data">
                  <IconButton onClick={handleExportData} disabled={!displayData || isLoading}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Compare Teams">
                  <IconButton onClick={handleCompareTeams} disabled={isLoading}>
                    <CompareArrowsIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            
            {isLoading ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="400px">
                <CircularProgress />
              </Box>
            ) : errorMessage && !displayData ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="400px" flexDirection="column" p={3}>
                <Typography color="error" gutterBottom>
                  Error loading shot data
                </Typography>
                <Typography color="textSecondary" variant="body2" align="center">
                  {errorMessage}
                </Typography>
                <Button variant="outlined" color="primary" sx={{ mt: 2 }} onClick={handleApplyFilters}>
                  Retry
                </Button>
              </Box>
            ) : !displayData ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="400px">
                <Typography color="textSecondary">No data available. Apply filters to see shots.</Typography>
              </Box>
            ) : (
              <ShotHeatmap 
                data={displayData.points} 
                width={isMobile ? 300 : 800} 
                height={isMobile ? 300 : 400} 
                showLabels={visualizationOptions.showLabels}
                colorScheme={visualizationOptions.colorScheme}
                maxValue={displayData.max_value}
              />
            )}
          </Paper>
          
          {/* Stats Cards */}
          {displayData && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      Total Shots
                    </Typography>
                    <Typography variant="h4">
                      {displayData.total_shots}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      Goals
                    </Typography>
                    <Typography variant="h4">
                      {displayData.total_goals}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      Avg. xG
                      <Tooltip title="Expected Goals - Probability of a shot resulting in a goal">
                        <InfoIcon fontSize="small" sx={{ ml: 1, verticalAlign: 'middle' }} />
                      </Tooltip>
                    </Typography>
                    <Typography variant="h4">
                      {displayData.average_xg.toFixed(3)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      Shooting %
                    </Typography>
                    <Typography variant="h4">
                      {((displayData.total_goals / displayData.total_shots) * 100).toFixed(1)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default ShotMap;