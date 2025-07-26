// frontend/src/components/MyPostCard.jsx
import React from 'react';
import { Card, CardMedia, CardContent, Typography, Box, Button, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { format } from 'date-fns';

const MyPostCard = ({ post, onHide, onDelete }) => {
    const imageUrl = post.photo_url || 'https://via.placeholder.com/400x300';
    const displayDate = post.updated_at || post.created_at;

    return (
        <Card
            sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                borderRadius: 3,
                boxShadow: 1,
                transition: 'all 0.3s ease',
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                },
            }}
        >
            <RouterLink to={`/posts/${post.id}`}>
                <CardMedia
                    component="img"
                    image={imageUrl}
                    alt={post.title}
                    sx={{
                        height: 200,
                        objectFit: 'cover',
                        width: '100%',
                    }}
                />
            </RouterLink>
            <CardContent
                sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    p: 2,
                }}
            >
                <Typography
                    variant="h6"
                    fontWeight="bold"
                    gutterBottom
                    sx={{
                        display: '-webkit-box',
                        WebkitBoxOrient: 'vertical',
                        WebkitLineClamp: 2,
                        overflow: 'hidden',
                    }}
                >
                    {post.title}
                </Typography>
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                        display: '-webkit-box',
                        WebkitBoxOrient: 'vertical',
                        WebkitLineClamp: 3,
                        overflow: 'hidden',
                    }}
                >
                    {post.summary}
                </Typography>
                <Box sx={{ flexGrow: 1 }} />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                    {displayDate ? format(new Date(displayDate), 'PPp') : '...'}
                </Typography>
            </CardContent>
            <Stack direction="row" spacing={1} sx={{ p: 2, pt: 0, borderTop: '1px solid #eee' }}>
                <Button component={RouterLink} to={`/edit-post/${post.id}`} size="small">Edit</Button>
                <Button onClick={() => onHide(post.id, post.is_hidden)} size="small" color={post.is_hidden ? "success" : "warning"}>
                    {post.is_hidden ? 'Show' : 'Hide'}
                </Button>
                <Box sx={{ flexGrow: 1 }} />
                <Button onClick={() => onDelete(post.id)} size="small" color="error">Delete</Button>
            </Stack>
        </Card>
    );
};

export default MyPostCard;
