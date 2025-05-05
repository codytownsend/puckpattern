import React, { useEffect, useState } from 'react';
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
  TextField,
  Button,
  Chip,
  Divider,
  Stack,
  Switch,
  FormControlLabel,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import InfoIcon from '@mui/icons-material/Info';

import ShotHeatmap from '../components/visualizations/ShotHeatmap';
import { 
  fetchShotHeatmap, 
  fetchShots, 
  fetchTeamComparison,
  selectShotHeatmap,
  selectShotsLoading,
  selectShotsError,
  setFilters,
  selectShotsFilters
} from '../store/slices/shotsSlice';
import { setVisualizationOption, selectVisualizationOptions } from '../store/slices/uiSlice';
import { AppDispatch } from '../store';

const ShotMap: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const heatmapData = useSelector(selectShotHeatmap);
  const isLoading = useSelector(selectShotsLoading);
  const error = useSelector(selectShotsError);
  const filters = useSelector(selectShotsFilters);
  const visualizationOptions = useSelector(selectVisualizationOptions);
  
  const [teams, setTeams] = useState<any[]>([
    { id: '1', name: 'Toronto Maple Leafs', abbreviation: 'TOR' },
    { id: '2', name: 'Boston Bruins', abbreviation: 'BOS' },
    { id: '3', name: 'Tampa Bay Lightning', abbreviation: 'TBL' },
    { id: '4', name: 'New York Rangers', abbreviation: 'NYR' },
    { id: '5', name: 'Colorado Avalanche', abbreviation: 'COL' }
  ]);
  
  const [players, setPlayers] = useState<any[]>([
    { id: '101', name: 'Auston Matthews', team_id: '1' },
    { id: '102', name: 'Mitch Marner', team_id: '1' },
    { id: '201', name: 'Patrice Bergeron', team_id: '2' },
    { id: '202', name: 'David Pastrnak', team_id: '2' },
    { id: '301', name: 'Nikita Kucherov', team_id: '3' },
    { id: '401', name: 'Artemi Panarin', team_id: '4' },
    { id: '501', name: 'Nathan MacKinnon', team_id: '5' }
  ]);
  
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [selectedPlayer, setSelectedPlayer] = useState<string>('');
  const [selectedSeason, setSelectedSeason] = useState<string>('2024-2025');
  
  const seasons = ['2023-2024', '2024-2025'];
  const shotTypes = ['All', 'Wrist Shot', 'Slap Shot', 'Snap Shot', 'Backhand', 'Tip-In', 'Deflection'];
  
  // Initialize by loading heatmap with default filters
  useEffect(() => {
    if (!heatmapData) {
      handleApplyFilters();
    }
  }, []);
  
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
  
  const handleVisualizationOptionChange = (option: keyof typeof visualizationOptions, value: any) => {
    dispatch(setVisualizationOption({ option, value }));
  };
  
  const handleApplyFilters = () => {
    // Prepare filters
    const newFilters = {
      team_id: selectedTeam || undefined,
      player_id: selectedPlayer || undefined,
      season: selectedSeason,
      normalize: visualizationOptions.normalizeData
    };
    
    // Update filters in store
    dispatch(setFilters(newFilters));
    
    // Fetch heatmap data
    dispatch(fetchShotHeatmap(newFilters));
  };
  
  const handleExportData = () => {
    if (!heatmapData) return;
    
    // Create CSV data
    const csvData = [
      ['x', 'y', 'value'],
      ...heatmapData.points.map(point => [point.x, point.y, point.value])
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
  };
  
  const handleCompareTeams = () => {
    // This would open a comparison modal in a full implementation
    console.log('Compare teams');
  };
  
  // Filter players based on selected team
  const filteredPlayers = selectedTeam 
    ? players.filter(player => player.team_id === selectedTeam) 
    : players;
  
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
            
            <Button 
              variant="contained" 
              fullWidth 
              color="primary" 
              onClick={handleApplyFilters}
              disabled={isLoading}
              startIcon={isLoading ? <CircularProgress size={24} color="inherit" /> : null}
            >
              Apply Filters
            </Button>
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
                  <IconButton onClick={handleExportData} disabled={!heatmapData || isLoading}>
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
            ) : error ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="400px">
                <Typography color="error">{error}</Typography>
              </Box>
            ) : !heatmapData ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="400px">
                <Typography color="textSecondary">No data available. Apply filters to see shots.</Typography>
              </Box>
            ) : (
              <ShotHeatmap 
                data={heatmapData.points} 
                width={800} 
                height={400} 
                showLabels={visualizationOptions.showLabels}
                colorScheme={visualizationOptions.colorScheme}
                maxValue={heatmapData.max_value}
              />
            )}
          </Paper>
          
          {/* Stats Cards */}
          {heatmapData && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      Total Shots
                    </Typography>
                    <Typography variant="h4">
                      {heatmapData.total_shots}
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
                      {heatmapData.total_goals}
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
                      {heatmapData.average_xg.toFixed(3)}
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
                      {((heatmapData.total_goals / heatmapData.total_shots) * 100).toFixed(1)}%
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