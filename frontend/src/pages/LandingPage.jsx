// frontend/src/pages/LandingPage.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { Container, Grid, Typography, Box, Select, MenuItem, FormControl, InputLabel, Stack, CircularProgress } from '@mui/material';
import api from '../api';
import PostCard from '../components/PostCard';
import SearchBar from '../components/SearchBar';
import HeroSection from '../components/HeroSection';

const LandingPage = () => {
    const [posts, setPosts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortOrder, setSortOrder] = useState('newest');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPosts = async () => {
            try {
                const response = await api.get('/posts/');
                setPosts(response.data);
            } catch (error) {
                console.error("Failed to fetch posts:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPosts();
    }, []);

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
        <>
            <HeroSection />
            <Container sx={{ py: 4 }} maxWidth="lg">
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 6, justifyContent: 'center', alignItems: 'center' }}>
                    <SearchBar onSearchChange={setSearchTerm} />
                    <FormControl sx={{ width: { xs: '100%', sm: 240 } }}>
                        <InputLabel id="sort-by-label">Sort By</InputLabel>
                        <Select labelId="sort-by-label" value={sortOrder} label="Sort By" onChange={(e) => setSortOrder(e.target.value)} sx={{ borderRadius: '12px' }}>
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
                                <PostCard post={post} />
                            </Grid>
                        ))
                    ) : (
                        <Typography sx={{ width: '100%', textAlign: 'center', mt: 4 }}>
                            No posts found.
                        </Typography>
                    )}
                </Grid>
            </Container>
        </>
    );
};

export default LandingPage;