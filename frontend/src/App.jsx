import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import RegisterModal from './components/RegisterModal';
import ProfileModal from './components/ProfileModal';
import AdminDashboard from './components/AdminDashboard';
import api from './api';
import { Box, CssBaseline, colors, ThemeProvider, createTheme, Typography, CircularProgress } from '@mui/material';

// --- Import All Page Components ---
import LandingPage from './pages/LandingPage';
import PostForm from './pages/PostForm';
import MyPosts from './pages/MyPosts';
import PostViewPage from './pages/PostViewPage';
import ChatPage from './pages/ChatPage';

// --- Global Theme Definition ---
const theme = createTheme({
  palette: {
    primary: { main: '#FDB813', contrastText: '#000000' },
    secondary: { main: colors.grey[800] },
    background: { default: '#FFFFFF' },
    text: { primary: '#111111', secondary: '#666666' }
  },
  typography: {
    fontFamily: 'Poppins, sans-serif',
    h1: { fontWeight: 700 }, h2: { fontWeight: 700 },
    h3: { fontWeight: 600 }, h4: { fontWeight: 600 },
  },
});

// --- Helper Component for Protected Routes ---
const ProtectedRoute = ({ user, children }) => {
    if (!user) {
        // If no user is logged in, redirect them to the homepage.
        return <Navigate to="/" replace />;
    }
    return children;
};

function App() {
  const [user, setUser] = useState(null);
  const [openRegisterModal, setOpenRegisterModal] = useState(false);
  const [openProfileModal, setOpenProfileModal] = useState(false);
  const [modalMode, setModalMode] = useState('register');
  const [loading, setLoading] = useState(true); // For initial app load

  // Fetches user data if a token exists. Wrapped in useCallback for stability.
  const fetchUserData = useCallback(async () => {
    const token = localStorage.getItem('riskwatch_token');
    if (token) {
      try {
        const response = await api.get('/users/me');
        setUser(response.data);
        if (!response.data.profile_complete) {
          setOpenProfileModal(true);
        }
      } catch (error) {
        console.error("Session could not be restored", error);
        localStorage.removeItem('riskwatch_token'); // Clean up invalid token
      }
    }
    setLoading(false);
  }, []);

  // Run once on initial application load
  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    if (!userData.profile_complete) {
      setOpenProfileModal(true);
    }
    setOpenRegisterModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('riskwatch_token');
    setUser(null);
    window.location.href = '/'; // Force a full refresh to clear all state
  };

  const handleOpenRegister = () => { setModalMode('register'); setOpenRegisterModal(true); };
  const handleOpenLogin = () => { setModalMode('login'); setOpenRegisterModal(true); };
  
  // Show a loading screen while checking for an existing session
  if (loading) {
    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <CircularProgress />
            <Typography variant="h6" sx={{ ml: 2 }}>Loading RiskWatch...</Typography>
        </Box>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ backgroundColor: 'background.default', color: 'text.primary', minHeight: '100vh' }}>
          <Navbar
            user={user}
            onRegisterClick={handleOpenRegister}
            onLoginClick={handleOpenLogin}
            onProfileClick={() => setOpenProfileModal(true)}
            onLogout={handleLogout}
          />
          <main>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/posts/:id" element={<PostViewPage />} />

              {/* Admin Route */}
              <Route 
                path="/admin" 
                element={
                    <ProtectedRoute user={user}>
                        {user?.role === 'admin' ? <AdminDashboard /> : <Navigate to="/" />}
                    </ProtectedRoute>
                } 
              />
              
              {/* Protected Routes for All Logged-in Users */}
              <Route path="/create-post" element={<ProtectedRoute user={user}><PostForm /></ProtectedRoute>} />
              <Route path="/edit-post/:id" element={<ProtectedRoute user={user}><PostForm /></ProtectedRoute>} />
              <Route path="/my-posts" element={<ProtectedRoute user={user}><MyPosts /></ProtectedRoute>} />
              <Route path="/chat" element={<ProtectedRoute user={user}><ChatPage user={user} /></ProtectedRoute>} />

              {/* Fallback Route - Redirects any unknown URL to the homepage */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </main>

          {/* Modals are rendered here to overlay on top of all pages */}
          <RegisterModal
            open={openRegisterModal}
            onClose={() => setOpenRegisterModal(false)}
            onLoginSuccess={handleLoginSuccess}
            initialMode={modalMode}
          />
          {user && (
            <ProfileModal
                open={openProfileModal}
                onClose={() => setOpenProfileModal(false)}
                user={user}
                onProfileUpdate={(updatedUser) => setUser(updatedUser)}
                onDataChange={fetchUserData} // This prop triggers a full user data refresh
            />
          )}
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;