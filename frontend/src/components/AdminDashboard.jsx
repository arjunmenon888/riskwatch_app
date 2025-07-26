// frontend/src/components/AdminDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import LockResetIcon from '@mui/icons-material/LockReset';
import api from '../api';

const AdminDashboard = () => {
    const [users, setUsers] = useState([]);
    const [error, setError] = useState('');

    const fetchUsers = async () => {
        try {
            const response = await api.get('/admin/users');
            setUsers(response.data);
        } catch (err) {
            setError('Failed to fetch users.');
            console.error(err);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleDelete = async (userId) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            try {
                await api.delete(`/admin/users/${userId}`);
                fetchUsers(); // Refresh the list
            } catch (err) {
                alert('Failed to delete user.');
            }
        }
    };

    const handleForceReset = async (userId) => {
        try {
            await api.post(`/admin/users/${userId}/force-reset`);
            alert('User has been marked for password reset on next login.');
            fetchUsers(); // Refresh to show updated flag status
        } catch (err) {
            alert('Failed to mark user for reset.');
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>Admin Dashboard</Typography>
            {error && <Typography color="error">{error}</Typography>}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Email</TableCell>
                            <TableCell>Company</TableCell>
                            <TableCell>Force Reset?</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {users.filter(u => u.role !== 'admin').map((user) => (
                            <TableRow key={user.id}>
                                <TableCell>{user.name}</TableCell>
                                <TableCell>{user.email}</TableCell>
                                <TableCell>{user.company || 'N/A'}</TableCell>
                                <TableCell>{user.force_reset ? 'Yes' : 'No'}</TableCell>
                                <TableCell>
                                    <IconButton onClick={() => handleForceReset(user.id)} title="Force Password Reset">
                                        <LockResetIcon color="warning" />
                                    </IconButton>
                                    <IconButton onClick={() => handleDelete(user.id)} title="Delete User">
                                        <DeleteIcon color="error" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};

export default AdminDashboard;