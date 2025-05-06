import React, { useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  AppBar, 
  Toolbar, 
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery,
  Tooltip,
  Avatar
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { selectSidebarOpen, setSidebarOpen } from '../../store/slices/uiSlice';
import { colors } from '../../styles/theme';

// Remove all icon imports

const drawerWidth = 240;

interface MainLayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  text: string;
  path: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const sidebarOpen = useSelector(selectSidebarOpen);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Close sidebar by default on mobile
  useEffect(() => {
    if (isMobile) {
      dispatch(setSidebarOpen(false));
    }
  }, [isMobile, dispatch]);

  const handleDrawerToggle = () => {
    dispatch(setSidebarOpen(!sidebarOpen));
  };

  // Simplified navigation without icons
  const navItems: NavItem[] = [
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

  // Determine if a nav item is active
  const isPathActive = (itemPath: string) => {
    if (itemPath === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(itemPath);
  };

  const drawer = (
    <>
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          p: 2 
        }}
      >
        <Typography variant="h6" color="white">PuckPattern</Typography>
        {isMobile && (
          <IconButton onClick={handleDrawerToggle} sx={{ color: 'white' }}>
            {/* Remove icon */}
          </IconButton>
        )}
      </Box>
      <Divider sx={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }} />
      <List sx={{ px: 1 }}>
        {navItems.map((item) => {
          const isActive = isPathActive(item.path);
          
          return (
            <ListItemButton
              key={item.text}
              selected={isActive}
              onClick={() => {
                navigate(item.path);
                if (isMobile) {
                  dispatch(setSidebarOpen(false));
                }
              }}
              sx={{
                mb: 0.5,
                borderRadius: 1,
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
              <ListItemText 
                primary={item.text} 
                sx={{ 
                  '& .MuiListItemText-primary': { 
                    fontSize: '0.95rem',
                    fontWeight: isActive ? 600 : 400
                  } 
                }} 
              />
            </ListItemButton>
          );
        })}
      </List>
      <Box sx={{ flexGrow: 1 }} /> {/* Spacer to push content to bottom */}
      <Divider sx={{ backgroundColor: 'rgba(255, 255, 255, 0.2)', mt: 'auto' }} />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
        <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.primary.light, color: 'black', fontSize: '0.875rem', mr: 1.5 }}>
          PP
        </Avatar>
        <Box>
          <Typography variant="body2" color="white">
            Demo Version
          </Typography>
          <Typography variant="caption" color="rgba(255, 255, 255, 0.7)">
            v0.1.0
          </Typography>
        </Box>
      </Box>
    </>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%' },
          ml: { sm: sidebarOpen ? `${drawerWidth}px` : 0 },
          backgroundColor: colors.primaryDark,
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          boxShadow: 1
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: sidebarOpen ? 'none' : 'block' } }}
          >
            {/* Remove icon */}
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navItems.find(item => isPathActive(item.path))?.text || 'PuckPattern'}
          </Typography>
          <Tooltip title="Help">
            <IconButton color="inherit">
              {/* Remove icon */}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ 
          width: { sm: drawerWidth }, 
          flexShrink: { sm: 0 },
        }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={isMobile && sidebarOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better performance on mobile
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              backgroundColor: colors.primaryDark,
              color: 'white'
            },
          }}
        >
          {drawer}
        </Drawer>
        
        {/* Desktop drawer - permanent or persistent based on sidebarOpen state */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              backgroundColor: colors.primaryDark,
              color: 'white',
              borderRight: '1px solid rgba(255, 255, 255, 0.12)',
              transform: !sidebarOpen ? `translateX(-${drawerWidth}px)` : 'none',
              visibility: !sidebarOpen ? 'hidden' : 'visible',
              transition: theme.transitions.create('transform', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
          open={sidebarOpen}
        >
          {drawer}
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{ 
          flexGrow: 1,
          p: 3,
          width: { 
            sm: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%' 
          },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          mt: { xs: '56px', sm: '64px' }, // Toolbar height
          backgroundColor: theme.palette.background.default,
        }}
      >
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default MainLayout;