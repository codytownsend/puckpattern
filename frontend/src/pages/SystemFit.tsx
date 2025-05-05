import React from 'react';
import ModulePlaceholder from './placeholder-modules';
import SportsSoccerIcon from '@mui/icons-material/SportsSoccer';

const SystemFit: React.FC = () => {
  return (
    <ModulePlaceholder 
      title="System Fit Engine" 
      description="Predict how players would perform in different tactical systems and team environments."
      icon={<SportsSoccerIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
    />
  );
};

export default SystemFit;