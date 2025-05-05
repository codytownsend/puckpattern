import React from 'react';
import ModulePlaceholder from './placeholder-modules';
import PeopleIcon from '@mui/icons-material/People';

const Players: React.FC = () => {
  return (
    <ModulePlaceholder 
      title="Player Intelligence Profiles" 
      description="Deep dive into player performance metrics, behavioral analytics, and role-based insights."
      icon={<PeopleIcon sx={{ fontSize: 100, color: 'primary.main', mb: 2, opacity: 0.7 }} />}
    />
  );
};

export default Players;