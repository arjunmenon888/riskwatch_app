// frontend/src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Grid, Box, Typography } from '@mui/material';
import api, { startChat } from '../api';
import ContactList from '../components/chat/ContactList';
import ChatWindow from '../components/chat/ChatWindow';

const ChatPage = ({ user }) => {
    const [rooms, setRooms] = useState([]);
    const [selectedRoom, setSelectedRoom] = useState(null);
    const [messages, setMessages] = useState([]);
    const ws = useRef(null);
    const selectedRoomRef = useRef(null);

    // Fetches chat rooms and optionally selects the first one.
    // Wrapped in useCallback to stabilize its identity across renders.
    const fetchRooms = useCallback(async (selectFirst = false) => {
        try {
            const response = await api.get('/chat/rooms');
            setRooms(response.data);
            if (selectFirst && response.data.length > 0 && !selectedRoomRef.current) {
                handleRoomSelect(response.data[0]);
            }
            return response.data;
        } catch (error) {
            console.error("Failed to fetch rooms", error);
        }
    }, []);

    // Sets the selected room and populates the message window with its history.
    const handleRoomSelect = (room) => {
        setSelectedRoom(room);
        setMessages(room.messages || []);
    };

    // Keeps the ref synchronized with the state for access within closures.
    useEffect(() => {
        selectedRoomRef.current = selectedRoom;
    }, [selectedRoom]);

    // This effect manages the WebSocket connection lifecycle.
    useEffect(() => {
        fetchRooms(true);

        const token = localStorage.getItem('riskwatch_token');
        if (!token) return;

        // Create a new WebSocket connection.
        const socket = new WebSocket(`ws://localhost:8000/ws/${token}`);
        ws.current = socket;

        socket.onopen = () => console.log("WebSocket connected");
        socket.onclose = () => console.log("WebSocket disconnected");
        socket.onerror = (error) => console.error("WebSocket error:", error);

        // Handles incoming messages.
        socket.onmessage = (event) => {
            const messageData = JSON.parse(event.data);
            // Uses the ref to check against the currently active room.
            if (messageData.room_id === selectedRoomRef.current?.id) {
                setMessages(prevMessages => [...prevMessages, messageData]);
            }
        };

        // Cleanup function to close the socket when the component unmounts.
        return () => {
            if (socket.readyState === 1) { // 1 means OPEN
                socket.close();
            }
        };
    }, [fetchRooms]);

    // Sends a message through the WebSocket and performs an optimistic update.
    const handleSendMessage = (content) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN && selectedRoom) {
            const messagePayload = {
                room_id: selectedRoom.id,
                content: content,
            };
            ws.current.send(JSON.stringify(messagePayload));

            // Optimistic UI update for a snappy user experience
            const tempMessage = {
                id: `temp-${Date.now()}`,
                sender_id: user.id,
                content: content,
                created_at: new Date().toISOString(),
                room_id: selectedRoom.id
            };
            setMessages(prevMessages => [...prevMessages, tempMessage]);
        }
    };
    
    // Creates a new chat room with a user found via search.
    const handleStartNewChat = async (recipientEmail) => {
        try {
            const newOrExistingRoom = await startChat(recipientEmail);
            if (!rooms.find(r => r.id === newOrExistingRoom.id)) {
                // Refresh the room list to include the new one
                await fetchRooms();
            }
            handleRoomSelect(newOrExistingRoom);
        } catch (error) {
            console.error("Failed to start new chat:", error);
            alert(error.response?.data?.detail || "Could not start chat. User may not exist.");
        }
    };

    return (
        <Box sx={{ height: 'calc(100vh - 65px)', display: 'flex', overflow: 'hidden' }}>
            <Box sx={{ width: { xs: '100%', sm: '30%', md: '25%' }, borderRight: '1px solid #eee', height: '100%', display: { xs: selectedRoom ? 'none' : 'block', sm: 'block' } }}>
                <ContactList 
                    rooms={rooms} 
                    onSelectRoom={handleRoomSelect} 
                    onStartNewChat={handleStartNewChat}
                    currentUserId={{ id: user.id, email: user.email }}
                    selectedRoomId={selectedRoom?.id}
                />
            </Box>
            <Box sx={{ flexGrow: 1, height: '100%', display: { xs: selectedRoom ? 'block' : 'none', sm: 'block' } }}>
                {selectedRoom ? (
                    <ChatWindow 
                        room={selectedRoom}
                        messages={messages} 
                        onSendMessage={handleSendMessage}
                        currentUserId={user.id}
                        onBack={() => setSelectedRoom(null)} // For mobile view
                    />
                ) : (
                    <Box sx={{ display: { xs: 'none', sm: 'flex'}, justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                        <Typography variant="h6" color="text.secondary">
                            Select a chat or search to start messaging
                        </Typography>
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default ChatPage;