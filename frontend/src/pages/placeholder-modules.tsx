import React from 'react';
import { Box, Typography, Paper, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ConstructionIcon from '@mui/icons-material/Construction';

// This is a template component for module pages that are still in development
const ModulePlaceholder: React.FC<{ title: string; description: string; icon?: React.ReactNode }> = ({ 
  title, 
  description, 
  icon 
}) => {
  const navigate = useNavigate();

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body1" color="textSecondary">
          {description}
        </Typography>
      </Box>

      <Paper
        elevation={3}
        sx={{
          p: 5,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: 700,
          mx: 'auto',
          my: 4
        }}
      >
        {icon || <ConstructionIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
        
        <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
          Module Under Development
        </Typography>
        
        <Typography variant="body1" color="textSecondary" align="center" paragraph sx={{ mb: 3 }}>
          This module is currently being developed. It will be available in a future update.
          In the meantime, you can explore our completed modules.
        </Typography>
        
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/')}
        >
          Back to Dashboard
        </Button>
      </Paper>
    </Box>
  );
};

export default ModulePlaceholder;