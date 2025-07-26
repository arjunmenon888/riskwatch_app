// frontend/src/pages/PostViewPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Box, Typography, CircularProgress, Paper, Divider } from '@mui/material';
import { format } from 'date-fns';
import api from '../api';

const PostViewPage = () => {
    const { id } = useParams();
    const [post, setPost] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPost = async () => {
            try {
                const response = await api.get(`/posts/${id}`);
                setPost(response.data);
            } catch (error) {
                console.error("Failed to fetch post:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPost();
    }, [id]);

    if (loading) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}><CircularProgress /></Box>;
    }

    if (!post) {
        return <Typography>Post not found.</Typography>;
    }

    const displayDate = post.updated_at || post.created_at;

    return (
        <Container maxWidth="md" sx={{ my: 4 }}>
            <Paper sx={{ p: { xs: 2, md: 4 } }}>
                <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
                    {post.title}
                </Typography>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                    Posted on {format(new Date(displayDate), 'PPP')}
                </Typography>
                <Box
                    component="img"
                    src={post.photo_url}
                    alt={post.title}
                    sx={{ width: '100%', height: 'auto', my: 3, borderRadius: 2 }}
                />
                <Typography variant="h5" gutterBottom>
                    {post.summary}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', my: 2 }}>
                    {post.description}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" >Contact Information</Typography>
                <Typography variant="body1">{post.contact_info}</Typography>
            </Paper>
        </Container>
    );
};

export default PostViewPage;