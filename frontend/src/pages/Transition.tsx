import React from 'react';
import ModulePlaceholder from './placeholder-modules';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

const Transition: React.FC = () => {
  return (
    <ModulePlaceholder 
      title="Transition Engine" 
      description="Analyze zone entries, exits, and neutral zone play patterns across teams and players."
      icon={<TrendingUpIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
    />
  );
};

export default Transition;