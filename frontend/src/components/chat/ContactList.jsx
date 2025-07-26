// frontend/src/components/chat/ContactList.jsx
import React, { useState, useEffect } from 'react';
import {
    Box,
    List,
    ListItemButton,
    ListItemAvatar,
    Avatar,
    ListItemText,
    Typography,
    TextField,
    Divider,
    CircularProgress
} from '@mui/material';
import { useDebounce } from 'use-debounce';
import { searchUsers } from '../../api';

const ContactList = ({ rooms, onSelectRoom, onStartNewChat, currentUserId, selectedRoomId }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [debouncedSearchQuery] = useDebounce(searchQuery, 400);

    useEffect(() => {
        const performSearch = async () => {
            if (debouncedSearchQuery.trim()) {
                setLoading(true);
                try {
                    const results = await searchUsers(debouncedSearchQuery);
                    setSearchResults(results);
                } catch (error) {
                    console.error("Failed to search users:", error);
                    setSearchResults([]);
                } finally {
                    setLoading(false);
                }
            } else {
                setSearchResults([]);
            }
        };
        performSearch();
    }, [debouncedSearchQuery]);

    const handleSelectSearchResult = (email) => {
        onStartNewChat(email);
        setSearchQuery('');
        setSearchResults([]);
    };

    const getOtherParticipant = (room) => {
        if (!room.participants) return null;
        return room.participants.find(p => p.id !== currentUserId.id);
    };

    return (
        <Box sx={{ borderRight: '1px solid #eee', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Chats</Typography>
                <TextField
                    fullWidth
                    variant="outlined"
                    size="small"
                    placeholder="Search by email to start chat..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    autoComplete="off"
                />
            </Box>
            <Divider />
            <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
                {loading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}><CircularProgress size={24} /></Box>}

                {searchQuery && !loading ? (
                    <List>
                        <Typography variant="caption" sx={{ px: 2, color: 'text.secondary' }}>Search Results</Typography>
                        {searchResults.length > 0 ? (
                            searchResults.map(user => (
                                <ListItemButton key={user.email} onClick={() => handleSelectSearchResult(user.email)}>
                                    <ListItemAvatar>
                                        <Avatar
                                            src={user.has_photo ? `http://localhost:8000/users/${user.id}/photo?t=${Date.now()}` : undefined}
                                            >
                                            {!user.has_photo && user.name.charAt(0).toUpperCase()}
                                        </Avatar>

                                    </ListItemAvatar>
                                    <ListItemText primary={user.name} secondary={user.email} />
                                </ListItemButton>
                            ))
                        ) : (
                            <Typography sx={{ p: 2, color: 'text.secondary' }}>No users found.</Typography>
                        )}
                    </List>
                ) : (
                    <List>
                        {rooms.map(room => {
                            const otherUser = getOtherParticipant(room);
                            if (!otherUser) return null;
                            return (
                                <ListItemButton
                                    key={room.id}
                                    onClick={() => onSelectRoom(room)}
                                    selected={selectedRoomId === room.id}
                                >
                                    <ListItemAvatar>
                                        <Avatar
                                            src={otherUser.has_photo ? `http://localhost:8000/users/${otherUser.id}/photo?t=${Date.now()}` : undefined}
                                            >
                                            {!otherUser.has_photo && otherUser.name.charAt(0).toUpperCase()}
                                            </Avatar>

                                    </ListItemAvatar>
                                    <ListItemText primary={otherUser.name} />
                                </ListItemButton>
                            );
                        })}
                    </List>
                )}
            </Box>
        </Box>
    );
};

export default ContactList;