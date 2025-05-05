import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper,
  Divider,
  FormControl,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  Button,
  Grid,
  TextField,
  InputLabel,
  Card,
  CardContent,
  Alert,
  Snackbar
} from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { 
  selectThemeMode, 
  setThemeMode, 
  selectVisualizationOptions,
  setVisualizationOption,
  resetVisualizationOptions
} from '../store/slices/uiSlice';

const Settings: React.FC = () => {
  const dispatch = useDispatch();
  const themeMode = useSelector(selectThemeMode);
  const visualizationOptions = useSelector(selectVisualizationOptions);
  
  const [showSuccess, setShowSuccess] = useState(false);
  
  const handleThemeModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setThemeMode(event.target.checked ? 'dark' : 'light'));
  };
  
  const handleVisualizationOptionChange = (option: keyof typeof visualizationOptions, value: any) => {
    dispatch(setVisualizationOption({ option, value }));
  };
  
  const handleResetVisualizationOptions = () => {
    dispatch(resetVisualizationOptions());
    setShowSuccess(true);
  };
  
  const handleSaveSettings = () => {
    // This would typically save to a backend or local storage
    setShowSuccess(true);
  };
  
  const handleSnackbarClose = () => {
    setShowSuccess(false);
  };
  
  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Configure application preferences and customize your experience
        </Typography>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Application Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Box mb={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={themeMode === 'dark'}
                    onChange={handleThemeModeChange}
                  />
                }
                label="Dark Mode"
              />
              <Typography variant="body2" color="textSecondary">
                Switch between light and dark theme
              </Typography>
            </Box>
            
            <Box mb={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="language-label">Language</InputLabel>
                <Select
                  labelId="language-label"
                  id="language-select"
                  value="en"
                  label="Language"
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Select your preferred language (Coming soon)
              </Typography>
            </Box>
            
            <Box mb={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="data-refresh-label">Data Refresh Rate</InputLabel>
                <Select
                  labelId="data-refresh-label"
                  id="data-refresh-select"
                  value="manual"
                  label="Data Refresh Rate"
                >
                  <MenuItem value="manual">Manual</MenuItem>
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="hourly">Hourly</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                How often to refresh data from the server
              </Typography>
            </Box>
            
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleSaveSettings}
            >
              Save Settings
            </Button>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Visualization Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Box mb={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={visualizationOptions.showLabels}
                    onChange={(e) => handleVisualizationOptionChange('showLabels', e.target.checked)}
                  />
                }
                label="Show Labels"
              />
              <Typography variant="body2" color="textSecondary">
                Display labels on visualizations
              </Typography>
            </Box>
            
            <Box mb={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={visualizationOptions.normalizeData}
                    onChange={(e) => handleVisualizationOptionChange('normalizeData', e.target.checked)}
                  />
                }
                label="Normalize Data"
              />
              <Typography variant="body2" color="textSecondary">
                Normalize data values in visualizations
              </Typography>
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
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Select color scheme for data visualizations
              </Typography>
            </Box>
            
            <Box mb={3}>
              <TextField
                fullWidth
                label="Grid Size"
                type="number"
                size="small"
                value={visualizationOptions.gridSize}
                onChange={(e) => handleVisualizationOptionChange('gridSize', parseInt(e.target.value))}
                InputProps={{ inputProps: { min: 5, max: 50 } }}
              />
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Set grid size for heatmaps (5-50)
              </Typography>
            </Box>
            
            <Button 
              variant="outlined" 
              color="secondary" 
              onClick={handleResetVisualizationOptions}
            >
              Reset to Defaults
            </Button>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" color="textSecondary">
                PuckPattern Demo Version
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Build: 0.1.0 (Development)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity="success"
          variant="filled"
        >
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;