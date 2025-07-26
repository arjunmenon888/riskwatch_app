// frontend/src/pages/MyPosts.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { Container, Grid, Typography, Button, Box, Select, MenuItem, FormControl, InputLabel, Stack, CircularProgress } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import api from '../api';
import MyPostCard from '../components/MyPostCard';
import SearchBar from '../components/SearchBar';

const MyPosts = () => {
    const [posts, setPosts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortOrder, setSortOrder] = useState('newest');
    const [loading, setLoading] = useState(true);

    const fetchMyPosts = async () => {
        setLoading(true);
        try {
            const response = await api.get('/posts/me');
            setPosts(response.data);
        } catch (error) {
            console.error("Failed to fetch your posts:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMyPosts();
    }, []);

    const handleHideToggle = async (postId) => {
        try {
            await api.patch(`/posts/${postId}/toggle-visibility`);
            fetchMyPosts();
        } catch (error) {
            console.error("Failed to toggle post visibility", error);
            alert("Could not update post visibility. Please try again.");
        }
    };

    const handleDelete = async (postId) => {
        if (window.confirm("Are you sure you want to permanently delete this post? This action cannot be undone.")) {
            try {
                await api.delete(`/posts/${postId}`);
                fetchMyPosts();
            } catch (error) {
                console.error("Failed to delete post", error);
                alert("Could not delete post. Please try again.");
            }
        }
    };

    const filteredAndSortedPosts = useMemo(() => {
        let filtered = [...posts];
        if (searchTerm) {
            const lowercasedTerm = searchTerm.toLowerCase();
            filtered = posts.filter(post =>
                post.title.toLowerCase().includes(lowercasedTerm) ||
                post.summary.toLowerCase().includes(lowercasedTerm)
            );
        }
        return filtered.sort((a, b) => {
            switch (sortOrder) {
                case 'oldest': return new Date(a.created_at) - new Date(b.created_at);
                case 'a-z': return a.title.localeCompare(b.title);
                case 'z-a': return b.title.localeCompare(a.title);
                case 'newest': default: return new Date(b.created_at) - new Date(a.created_at);
            }
        });
    }, [posts, searchTerm, sortOrder]);

    if (loading) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}><CircularProgress /></Box>;
    }

    return (
        <Container sx={{ py: 4 }} maxWidth="lg">
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
                <Typography variant="h4" component="h1" fontWeight="bold">My Posts</Typography>
                <Button component={RouterLink} to="/create-post" variant="contained">
                    Create New Post
                </Button>
            </Stack>
            
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 6, justifyContent: 'center', alignItems: 'center' }}>
                <SearchBar onSearchChange={setSearchTerm} />
                <FormControl sx={{ width: { xs: '100%', sm: 240 } }}>
                    <InputLabel id="sort-by-label-my-posts">Sort By</InputLabel>
                    <Select labelId="sort-by-label-my-posts" value={sortOrder} label="Sort By" onChange={(e) => setSortOrder(e.target.value)} sx={{ borderRadius: '12px' }}>
                        <MenuItem value="newest">Most Recent</MenuItem>
                        <MenuItem value="oldest">Oldest First</MenuItem>
                        <MenuItem value="a-z">Title: A–Z</MenuItem>
                        <MenuItem value="z-a">Title: Z–A</MenuItem>
                    </Select>
                </FormControl>
            </Stack>

            {/* --- CORRECT GRID IMPLEMENTATION --- */}
            <Grid container spacing={4} alignItems="stretch">
                {filteredAndSortedPosts.length > 0 ? (
                    filteredAndSortedPosts.map((post) => (
                        <Grid item key={post.id} xs={12} sm={6} lg={4}>
                            <MyPostCard 
                                post={post} 
                                onHide={handleHideToggle} 
                                onDelete={handleDelete} 
                            />
                        </Grid>
                    ))
                ) : (
                    <Typography sx={{ width: '100%', textAlign: 'center', mt: 4 }}>
                        You have not created any posts yet.
                    </Typography>
                )}
            </Grid>
        </Container>
    );
};

export default MyPosts;