import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Provider } from 'react-redux';
import store from './store';
import theme from './styles/theme';
import MainLayout from './components/layout/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import ShotMap from './pages/ShotMap';
import PowerPlay from './pages/PowerPlay';
import TeamStrategy from './pages/TeamStrategy';
import Players from './pages/Players';
import Transition from './pages/Transition';
import GameAnalysis from './pages/GameAnalysis';
import SystemFit from './pages/SystemFit';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <MainLayout>
            <Routes>
              {/* Make sure there's an exact path for the root */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/shots" element={<ShotMap />} />
              <Route path="/powerplay" element={<PowerPlay />} />
              <Route path="/team-strategy" element={<TeamStrategy />} />
              <Route path="/players" element={<Players />} />
              <Route path="/transition" element={<Transition />} />
              <Route path="/games" element={<GameAnalysis />} />
              <Route path="/system-fit" element={<SystemFit />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </MainLayout>
        </Router>
      </ThemeProvider>
    </Provider>
  );
}

export default App;