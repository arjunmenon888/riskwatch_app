// frontend/src/components/PostCard.jsx
import React from 'react';
import { Card, CardMedia, CardContent, Typography, Box, Link as MuiLink } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { format } from 'date-fns';

const PostCard = ({ post }) => {
    const imageUrl = post.photo_url || 'https://via.placeholder.com/400x300';
    const displayDate = post.updated_at || post.created_at;

    return (
        <MuiLink
            component={RouterLink}
            to={`/posts/${post.id}`}
            sx={{
                textDecoration: 'none',
                color: 'inherit',
                display: 'block',
                height: '100%',
            }}
        >
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
                <CardContent
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        flexGrow: 1,
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
                    <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 1 }}
                    >
                        {displayDate ? format(new Date(displayDate), 'PPp') : '...'}
                    </Typography>
                </CardContent>
            </Card>
        </MuiLink>
    );
};

export default PostCard;
