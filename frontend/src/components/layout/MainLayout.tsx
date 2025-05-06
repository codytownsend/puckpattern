import React, { useState } from 'react';
import { 
  Box, 
  Drawer, 
  AppBar, 
  Toolbar, 
  Typography, 
  Divider, 
  IconButton, 
  List, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText,
  useTheme,
  CssBaseline,
  Container
} from '@mui/material';
import { styled } from '@mui/material/styles';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AssessmentIcon from '@mui/icons-material/Assessment';
import BarChartIcon from '@mui/icons-material/BarChart';
import PeopleIcon from '@mui/icons-material/People';
import SportsSoccerIcon from '@mui/icons-material/SportsSoccer';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import BubbleChartIcon from '@mui/icons-material/BubbleChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import SettingsIcon from '@mui/icons-material/Settings';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { selectSidebarOpen, setSidebarOpen } from '../../store/slices/uiSlice';

const drawerWidth = 240;

interface MainLayoutProps {
  children: React.ReactNode;
}

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })<{
  open?: boolean;
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: `-${drawerWidth}px`,
  ...(open && {
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  }),
}));

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const sidebarOpen = useSelector(selectSidebarOpen);

  const handleDrawerOpen = () => {
    dispatch(setSidebarOpen(true));
  };

  const handleDrawerClose = () => {
    dispatch(setSidebarOpen(false));
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Shot & Chance Map', icon: <BubbleChartIcon />, path: '/shots' },
    { text: 'Power Play Decoder', icon: <AssessmentIcon />, path: '/powerplay' },
    { text: 'Team Strategy', icon: <CompareArrowsIcon />, path: '/team-strategy' },
    { text: 'Player Intelligence', icon: <PeopleIcon />, path: '/players' },
    { text: 'Transition Engine', icon: <TrendingUpIcon />, path: '/transition' },
    { text: 'Game Analysis', icon: <BarChartIcon />, path: '/games' },
    { text: 'System Fit', icon: <SportsSoccerIcon />, path: '/system-fit' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${sidebarOpen ? drawerWidth : 0}px)`,
          ml: `${sidebarOpen ? drawerWidth : 0}px`,
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          backgroundColor: theme.palette.primary.dark,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            edge="start"
            sx={{
              marginRight: 5,
              ...(sidebarOpen ? { display: 'none' } : {}),
            }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            PuckPattern
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            backgroundColor: theme.palette.primary.dark,
            color: theme.palette.common.white,
          },
        }}
        variant="persistent"
        anchor="left"
        open={Boolean(sidebarOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', padding: theme.spacing(0, 1), ...theme.mixins.toolbar, justifyContent: 'flex-end' }}>
          <Typography variant="h6" sx={{ flexGrow: 1, padding: theme.spacing(0, 2) }}>
            PuckPattern
          </Typography>
          <IconButton onClick={handleDrawerClose} sx={{ color: theme.palette.common.white }}>
            <ChevronLeftIcon />
          </IconButton>
        </Box>
        <Divider sx={{ backgroundColor: theme.palette.grey[700] }} />
        <List>
          {menuItems.map((item) => (
            <ListItemButton
              key={item.text} 
              onClick={() => navigate(item.path)}
              selected={location.pathname === item.path}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'rgba(151, 223, 252, 0.2)',
                  '&:hover': {
                    backgroundColor: 'rgba(151, 223, 252, 0.3)',
                  }
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                }
              }}
            >
              <ListItemIcon sx={{ color: theme.palette.common.white }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Main open={Boolean(sidebarOpen)}>
        <Box sx={{ height: { xs: 56, sm: 64 } }} /> {/* Toolbar spacer */}
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {children}
        </Container>
      </Main>
    </Box>
  );
};

export default MainLayout;