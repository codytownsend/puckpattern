import React from 'react';
import ModulePlaceholder from './placeholder-modules';
import BarChartIcon from '@mui/icons-material/BarChart';

const GameAnalysis: React.FC = () => {
  return (
    <ModulePlaceholder 
      title="Game Analysis" 
      description="Comprehensive analysis of individual games, including key metrics, momentum shifts, and tactical insights."
      icon={<BarChartIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
    />
  );
};

export default GameAnalysis;