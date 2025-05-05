import React from 'react';
import ModulePlaceholder from './placeholder-modules';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';

const TeamStrategy: React.FC = () => {
  return (
    <ModulePlaceholder 
      title="Team Strategy Profiles" 
      description="Visualize and analyze team tactical fingerprints, playing styles, and strategic patterns."
      icon={<CompareArrowsIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
    />
  );
};

export default TeamStrategy;