import React, { useState, useEffect } from 'react';
import { Container, Box, Typography, TextField, Button, CircularProgress } from '@mui/material';
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom';
import api from '../api';

const PostForm = () => {
    const { id } = useParams(); // Get post ID from URL if it exists
    const isEditing = Boolean(id);
    const navigate = useNavigate();

    // State for form fields
    const [formData, setFormData] = useState({
        title: '',
        summary: '',
        description: '',
        contact_info: '',
    });
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false); // For submission spinner
    const [formLoading, setFormLoading] = useState(true); // For initial data fetch
    const [error, setError] = useState('');

    // --- NEW: useEffect to fetch post data for editing ---
    useEffect(() => {
        const fetchPostData = async () => {
            if (isEditing) {
                try {
                    const response = await api.get(`/posts/${id}`);
                    const post = response.data;
                    // Pre-fill the form with the fetched data
                    setFormData({
                        title: post.title,
                        summary: post.summary,
                        description: post.description,
                        contact_info: post.contact_info,
                    });
                } catch (err) {
                    console.error("Failed to fetch post data", err);
                    setError("Could not load post data. Please try again.");
                } finally {
                    setFormLoading(false); // Finished loading
                }
            } else {
                setFormLoading(false); // Not editing, so not loading
            }
        };

        fetchPostData();
    }, [id, isEditing]); // Rerun if the ID changes

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        // Image is only required for new posts
        if (!file && !isEditing) {
            setError('An image is required to create a post.');
            return;
        }
        setLoading(true);
        setError('');

        try {
            if (isEditing) {
                // --- NEW: Handle UPDATE (PUT request) ---
                // We send only the text data for an update. Image updates would be a separate feature.
                await api.put(`/posts/${id}`, formData);
            } else {
                // --- Handle CREATE (POST request with FormData) ---
                const postData = new FormData();
                postData.append('title', formData.title);
                postData.append('summary', formData.summary);
                postData.append('description', formData.description);
                postData.append('contact_info', formData.contact_info);
                postData.append('file', file);
                
                await api.post('/posts/', postData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
            }
            // Navigate to My Posts page on success
            navigate('/my-posts');
        } catch (err) {
            setError('Failed to submit post. Please check your inputs and try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Show a loading spinner while fetching data for an edit
    if (formLoading) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}><CircularProgress /></Box>;
    }

    return (
        <Container maxWidth="md">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" gutterBottom fontWeight="bold">{isEditing ? 'Edit Post' : 'Create a New Post'}</Typography>
                <Button component={RouterLink} to="/my-posts" sx={{ mb: 2 }}>← Back to My Posts</Button>
                <form onSubmit={handleSubmit}>
                    <TextField name="title" label="Title" value={formData.title} onChange={handleChange} fullWidth required margin="normal" />
                    <TextField name="summary" label="Summary (max 150 chars)" value={formData.summary} onChange={handleChange} fullWidth required margin="normal" inputProps={{ maxLength: 150 }} helperText={`${formData.summary.length}/150`} />
                    <TextField name="description" label="Full Description" value={formData.description} onChange={handleChange} fullWidth required margin="normal" multiline rows={4} />
                    <TextField name="contact_info" label="Contact Info (Email or Phone)" value={formData.contact_info} onChange={handleChange} fullWidth required margin="normal" />
                    
                    <Typography sx={{ mt: 2 }}>{isEditing ? 'Upload New Image (Optional)' : 'Post Image *'}</Typography>
                    <input type="file" accept="image/*" onChange={handleFileChange} required={!isEditing} />
                    <Typography variant="caption" display="block" color="text.secondary">
                        {isEditing && "Leave blank to keep the current image."}
                    </Typography>

                    {error && <Typography color="error" sx={{ my: 2 }}>{error}</Typography>}

                    <Button type="submit" variant="contained" sx={{ mt: 3 }} disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : (isEditing ? 'Save Changes' : 'Submit Post')}
                    </Button>
                </form>
            </Box>
        </Container>
    );
};

export default PostForm;