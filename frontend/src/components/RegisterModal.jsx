import React, { useState, useEffect } from 'react';
import { Modal, Box, Typography, TextField, Button, Link } from '@mui/material';
import api from '../api';

const RegisterModal = ({ open, onClose, onLoginSuccess, initialMode = 'register' }) => {
  // `isLogin` determines which form (Login or Register) is shown.
  const [isLogin, setIsLogin] = useState(initialMode === 'login');
  
  // State for the form fields and any error messages.
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');

  // This `useEffect` hook runs whenever the modal is opened or the initial mode changes.
  // It resets the form to a clean state.
  useEffect(() => {
    if (open) {
      setIsLogin(initialMode === 'login');
      setError('');
      setFormData({
        name: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: '',
      });
    }
  }, [open, initialMode]);

  // Handles changes in any of the form's text fields.
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Handles the form submission for both Login and Register.
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (isLogin) {
      // --- LOGIN LOGIC ---
      try {
        const response = await api.post('/login', {
          email: formData.email,
          password: formData.password,
        });
        localStorage.setItem('riskwatch_token', response.data.access_token);
        onLoginSuccess(response.data.user); // Pass user data up to App.jsx
        onClose(); // Close the modal on success
      } catch (err) {
        setError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
      }
    } else {
      // --- REGISTER LOGIC ---
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      try {
        // 1. Register the new user
        await api.post('/register', {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          password: formData.password,
        });
        // 2. Automatically log the new user in
        const loginResponse = await api.post('/login', {
          email: formData.email,
          password: formData.password,
        });
        localStorage.setItem('riskwatch_token', loginResponse.data.access_token);
        onLoginSuccess(loginResponse.data.user); // Pass user data up
        onClose(); // Close the modal on success
      } catch (err) {
        setError(err.response?.data?.detail || 'Registration failed.');
      }
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'background.paper', boxShadow: 24, p: 4, borderRadius: 2 }}>
        <Typography variant="h6">{isLogin ? 'Login' : 'Register'}</Typography>
        
        <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
          {/* These fields only show for registration */}
          {!isLogin && (
            <>
              <TextField margin="normal" required fullWidth label="Name" name="name" value={formData.name} onChange={handleChange} />
              <TextField margin="normal" required fullWidth label="Mobile Phone" name="phone" value={formData.phone} onChange={handleChange} />
            </>
          )}
          
          {/* These fields are common to both forms */}
          <TextField margin="normal" required fullWidth label="Email Address" name="email" type="email" value={formData.email} onChange={handleChange} autoFocus />
          <TextField margin="normal" required fullWidth label="Password" name="password" type="password" value={formData.password} onChange={handleChange} />

          {/* This field only shows for registration */}
          {!isLogin && (
            <TextField margin="normal" required fullWidth label="Confirm Password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} />
          )}
          
          {/* Display any error messages */}
          {error && <Typography color="error" sx={{mt: 2}}>{error}</Typography>}
          
          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2, py: 1.5, fontWeight: 'bold' }}>
            {isLogin ? 'Login' : 'Register'}
          </Button>
          
          {/* Link to toggle between Login and Register views */}
          <Link component="button" type="button" variant="body2" onClick={() => { setIsLogin(!isLogin); setError(''); }}>
            {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
          </Link>
        </Box>
      </Box>
    </Modal>
  );
};

export default RegisterModal;