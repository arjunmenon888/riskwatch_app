import React, { useState, useEffect } from 'react';
import {
    Modal,
    Box,
    Typography,
    TextField,
    Button,
    CircularProgress
} from '@mui/material';
import api from '../api';

const ProfileModal = ({ open, onClose, user, onProfileUpdate, onDataChange }) => {
    // State to manage the form fields
    const [profileData, setProfileData] = useState({
        name: '',
        email: '',
        phone: '',
        company: '',
        designation: '',
    });
    
    // State for the selected photo file and UI feedback
    const [photoFile, setPhotoFile] = useState(null);
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    // This effect pre-fills the form when the modal opens or the user data changes
    useEffect(() => {
        if (user) {
            setProfileData({
                name: user.name || '',
                email: user.email || '',
                phone: user.phone || '',
                company: user.company || '',
                designation: user.designation || '',
            });
            // Show a helpful message for first-time profile completion
            if (!user.profile_complete) {
                setMessage('Please complete your profile to continue.');
            } else {
                setMessage(''); // Clear message for regular edits
            }
        }
    }, [user, open]); // Re-run when the user object or open state changes

    const handleChange = (e) => {
        setProfileData({ ...profileData, [e.target.name]: e.target.value });
    };
  
    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setPhotoFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');

        try {
            // First, update the text-based profile data
            const response = await api.put('/users/me', profileData);
            
            // If a new photo file was selected, upload it
            if (photoFile) {
                const formData = new FormData();
                formData.append('file', photoFile);
                await api.post('/users/me/photo', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
                
                // IMPORTANT: After a new photo is uploaded, trigger a full data refresh
                // This tells App.jsx to call fetchUserData() again
                if (onDataChange) {
                    onDataChange();
                }
            }
            
            // Update the user state in App.jsx with the new text data for a fast UI response
            onProfileUpdate(response.data);
            setMessage('Profile updated successfully!');
            
            // Close the modal after a short delay to let the user see the success message
            setTimeout(() => {
                onClose();
            }, 1500);

        } catch (error) {
            setMessage('Failed to update profile. Please try again.');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal open={open} onClose={onClose}>
            <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 400, bgcolor: 'background.paper', boxShadow: 24, p: 4, borderRadius: 2 }}>
                <Typography variant="h6" component="h2">Edit Profile</Typography>
                
                {message && (
                    <Typography 
                        color={message.includes('success') ? 'primary.main' : 'error'} 
                        sx={{ my: 2 }}
                    >
                        {message}
                    </Typography>
                )}

                <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
                    <TextField margin="normal" required fullWidth label="Name" name="name" value={profileData.name} onChange={handleChange} />
                    <TextField margin="normal" required fullWidth label="Email Address" name="email" value={profileData.email} onChange={handleChange} />
                    <TextField margin="normal" required fullWidth label="Phone" name="phone" value={profileData.phone} onChange={handleChange} />
                    <TextField margin="normal" fullWidth label="Company (Optional)" name="company" value={profileData.company} onChange={handleChange} />
                    <TextField margin="normal" fullWidth label="Designation (Optional)" name="designation" value={profileData.designation} onChange={handleChange} />
                    
                    <Typography sx={{ mt: 2, mb: 1 }}>Profile Photo (Optional)</Typography>
                    <input type="file" accept="image/*" onChange={handleFileChange} />
                    <Typography variant="caption" display="block" color="text.secondary">
                        Leave blank to keep your current photo.
                    </Typography>

                    <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }} disabled={loading}>
                        {loading ? <CircularProgress size={24} color="inherit" /> : 'Save Changes'}
                    </Button>
                </Box>
            </Box>
        </Modal>
    );
};

export default ProfileModal;