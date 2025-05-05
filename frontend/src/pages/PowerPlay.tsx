import React from 'react';
import ModulePlaceholder from './placeholder-modules';
import AssessmentIcon from '@mui/icons-material/Assessment';

const PowerPlay: React.FC = () => {
  return (
    <ModulePlaceholder 
      title="Power Play Decoder" 
      description="Analyze power play formations, tendencies, and effectiveness across teams and players."
      icon={<AssessmentIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
    />
  );
};

export default PowerPlay;