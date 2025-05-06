import React from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  AppBar, 
  Toolbar, 
  Button,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Divider
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { selectSidebarOpen, setSidebarOpen } from '../../store/slices/uiSlice';

const drawerWidth = 240;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const sidebarOpen = useSelector(selectSidebarOpen);

  const handleDrawerToggle = () => {
    dispatch(setSidebarOpen(!sidebarOpen));
  };

  // Log the current path to debug
  console.log("Current path:", location.pathname);

  const navItems = [
    { text: 'Dashboard', path: '/' },
    { text: 'Shot & Chance Map', path: '/shots' },
    { text: 'Power Play Decoder', path: '/powerplay' },
    { text: 'Team Strategy', path: '/team-strategy' },
    { text: 'Player Intelligence', path: '/players' },
    { text: 'Transition Engine', path: '/transition' },
    { text: 'Game Analysis', path: '/games' },
    { text: 'System Fit', path: '/system-fit' },
    { text: 'Settings', path: '/settings' }
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: '#2E2E38'
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            PuckPattern
          </Typography>
          <Button color="inherit" onClick={handleDrawerToggle} sx={{ display: { sm: 'none' } }}>
            Menu
          </Button>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              backgroundColor: '#2E2E38',
              color: 'white'
            },
          }}
          open
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6">PuckPattern</Typography>
          </Box>
          <Divider sx={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }} />
          <List>
            {navItems.map((item) => {
              // Exact path matching for root path, includes matching for others
              const isSelected = item.path === '/' 
                ? location.pathname === '/' 
                : location.pathname.includes(item.path);
                
              return (
                <ListItemButton
                  key={item.text}
                  selected={isSelected}
                  onClick={() => navigate(item.path)}
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
                  <ListItemText primary={item.text} />
                </ListItemButton>
              );
            })}
          </List>
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{ 
          flexGrow: 1, 
          p: 3, 
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` }
        }}
      >
        <Toolbar /> {/* This provides spacing below the AppBar */}
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default MainLayout;