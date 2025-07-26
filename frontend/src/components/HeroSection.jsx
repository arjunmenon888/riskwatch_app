// frontend/src/components/HeroSection.jsx
import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const HeroSection = () => {
  return (
    // Container is now full-width with side padding
    <Container maxWidth={false} sx={{ px: { xs: 2, md: 4 } }}>
      <Box sx={{ my: 12, textAlign: 'center' }}>
        <Typography 
          variant="h1" 
          component="h1" 
          sx={{ mb: 2, fontSize: { xs: '3rem', md: '4.5rem' }, fontWeight: 700 }}
        >
          RiskWatch
        </Typography>
        <Typography 
          variant="h5" 
          component="p" 
          color="text.secondary" 
          sx={{ fontSize: { xs: '1.2rem', md: '1.5rem' } }}
        >
          Health, Safety, Environment
        </Typography>
      </Box>
    </Container>
  );
};

export default HeroSection;