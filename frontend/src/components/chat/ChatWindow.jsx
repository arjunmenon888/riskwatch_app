import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography, TextField, IconButton, Paper, Avatar, Tooltip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import InsertEmoticonIcon from '@mui/icons-material/InsertEmoticon';
import { format } from 'date-fns';
import Picker from '@emoji-mart/react';
import data from '@emoji-mart/data';

const ChatWindow = ({ room, messages, onSendMessage, currentUserId }) => {
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const [uploading, setUploading] = useState(false);
    const [pendingFiles, setPendingFiles] = useState([]);
    const [previews, setPreviews] = useState([]);
    const [message, setMessage] = useState('');
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();

        if (pendingFiles.length > 0) {
            setUploading(true);
            for (const file of pendingFiles) {
                const formData = new FormData();
                formData.append("file", file);
                formData.append("room_id", room.id);

                const token = localStorage.getItem("riskwatch_token");
                const res = await fetch("http://localhost:8000/chat/upload", {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` },
                    body: formData
                });
                const data = await res.json();

                if (data.id) {
                    onSendMessage(`[file:${file.name}|${data.id}]`);
                }
            }
            setPendingFiles([]);
            setPreviews([]);
            setUploading(false);
            return;
        }

        if (message.trim()) {
            onSendMessage(message);
            setMessage('');
        }
    };

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        previewFiles(files);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files);
        previewFiles(files);
    };

    const previewFiles = (files) => {
        setPendingFiles(prev => [...prev, ...files]);

        const newPreviews = files.map(file => {
            if (file.type.startsWith('image/')) {
                return { url: URL.createObjectURL(file), name: file.name, type: 'image' };
            } else {
                return { name: file.name, type: 'file' };
            }
        });

        setPreviews(prev => [...prev, ...newPreviews]);
    };

    const handleEmojiSelect = (emoji) => {
        setMessage(prev => prev + emoji.native);
    };

    const removeFile = (index) => {
        setPendingFiles(pendingFiles.filter((_, i) => i !== index));
        setPreviews(previews.filter((_, i) => i !== index));
    };

    const otherUser = room.participants.find(p => p.id !== currentUserId);

    const formatDateLabel = (date) => {
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);

        if (date.toDateString() === today.toDateString()) return "Today";
        if (date.toDateString() === yesterday.toDateString()) return "Yesterday";

        return date.toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: date.getFullYear() !== today.getFullYear() ? "numeric" : undefined
        });
    };

    return (
        <Box
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}
        >
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2, borderBottom: '1px solid #eee' }} elevation={0}>
                <Avatar src={otherUser?.has_photo ? `http://localhost:8000/users/${otherUser.id}/photo?t=${Date.now()}` : undefined}>
                    {!otherUser?.has_photo && otherUser?.name.charAt(0).toUpperCase()}
                </Avatar>
                <Typography variant="h6">{otherUser?.name}</Typography>
            </Paper>

            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, backgroundColor: '#f9f9f9' }}>
                {messages.map((msg, index) => {
                    const currentDate = new Date(msg.created_at);
                    const previousDate = index > 0 ? new Date(messages[index - 1].created_at) : null;
                    const isNewDate = !previousDate || currentDate.toDateString() !== previousDate.toDateString();

                    return (
                        <React.Fragment key={msg.id}>
                            {isNewDate && (
                                <Typography variant="caption" align="center" sx={{ display: 'block', textAlign: 'center', my: 2, color: 'text.secondary' }}>
                                    {formatDateLabel(currentDate)}
                                </Typography>
                            )}
                            <Box sx={{ display: 'flex', justifyContent: msg.sender_id === currentUserId ? 'flex-end' : 'flex-start', mb: 2 }}>
                                <Paper
                                    elevation={1}
                                    sx={{
                                        p: 1.5,
                                        backgroundColor: msg.sender_id === currentUserId ? 'primary.main' : 'white',
                                        color: msg.sender_id === currentUserId ? 'primary.contrastText' : 'text.primary',
                                        borderRadius: '16px',
                                        borderTopRightRadius: msg.sender_id === currentUserId ? '4px' : '16px',
                                        borderTopLeftRadius: msg.sender_id !== currentUserId ? '4px' : '16px',
                                        maxWidth: '70%',
                                    }}
                                >
                                    <Typography variant="body1" sx={{ wordBreak: 'break-word' }}>
                                        {msg.content.startsWith('[file:') ? (() => {
                                            const match = msg.content.match(/\[file:(.+?)\|(.*?)\]/);
                                            if (!match) return msg.content;
                                            const [_, filename, fileId] = match;
                                            const fileUrl = `http://localhost:8000/chat/file/${fileId}`;
                                            const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(filename);
                                            return isImage ? (
                                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                    <img src={fileUrl} alt={filename} style={{ maxWidth: 200, maxHeight: 200, borderRadius: 8 }} />
                                                    <Typography variant="caption" align="center">{filename}</Typography>
                                                </Box>
                                            ) : (
                                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                    <AttachFileIcon fontSize="large" />
                                                    <a href={fileUrl} target="_blank" rel="noopener noreferrer" style={{ textAlign: 'center', wordBreak: 'break-word' }}>{filename}</a>
                                                </Box>
                                            );
                                        })() : msg.content}
                                    </Typography>
                                    <Typography variant="caption" sx={{ display: 'block', textAlign: 'right', mt: 0.5, opacity: 0.8 }}>
                                        {format(currentDate, 'p')}
                                    </Typography>
                                </Paper>
                            </Box>
                        </React.Fragment>
                    );
                })}
                <div ref={messagesEndRef} />
            </Box>

            <Box component="form" onSubmit={handleSend} sx={{ p: 2, borderTop: '1px solid #ddd', backgroundColor: '#fff' }}>
                {previews.map((file, index) => (
                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        {file.type === 'image' ? (
                            <img src={file.url} alt={file.name} style={{ maxHeight: 80, borderRadius: 4 }} />
                        ) : (
                            <AttachFileIcon />
                        )}
                        <Typography variant="body2">{file.name}</Typography>
                        <IconButton size="small" onClick={() => removeFile(index)}>❌</IconButton>
                    </Box>
                ))}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Tooltip title="Attach File">
                        <IconButton component="label">
                            <AttachFileIcon />
                            <input type="file" hidden multiple onChange={handleFileSelect} ref={fileInputRef} />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Emoji">
                        <IconButton onClick={() => setShowEmojiPicker(!showEmojiPicker)}>
                            <InsertEmoticonIcon />
                        </IconButton>
                    </Tooltip>
                    <TextField
                        name="message"
                        fullWidth
                        variant="outlined"
                        placeholder={uploading ? "Uploading files..." : "Type a message..."}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        disabled={uploading}
                        autoComplete="off"
                        sx={{ '& .MuiOutlinedInput-root': { borderRadius: '20px' } }}
                    />
                    <IconButton type="submit" color="primary" disabled={uploading}>
                        <SendIcon />
                    </IconButton>
                </Box>
                {showEmojiPicker && (
                    <Box sx={{ position: 'absolute', bottom: 70, right: 20, zIndex: 10 }}>
                        <Picker data={data} onEmojiSelect={handleEmojiSelect} theme="light" />
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default ChatWindow;
