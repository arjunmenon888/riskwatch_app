import React, { useState } from 'react';
import {
    AppBar,
    Toolbar,
    Button,
    Box,
    IconButton,
    Avatar,
    Container,
    Typography,
    Stack,
    Link,
    Menu,
    MenuItem,
    Divider,
    Tooltip
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import LogoutIcon from '@mui/icons-material/Logout';
import PersonIcon from '@mui/icons-material/Person';
import ForumIcon from '@mui/icons-material/Forum';

const Navbar = ({ user, onRegisterClick, onLoginClick, onProfileClick, onLogout }) => {
    const [anchorElServices, setAnchorElServices] = useState(null);
    const [anchorElProfile, setAnchorElProfile] = useState(null);
    const navigate = useNavigate();

    const isServicesOpen = Boolean(anchorElServices);
    const isProfileOpen = Boolean(anchorElProfile);

    const handleServicesClick = (event) => {
        setAnchorElServices(event.currentTarget);
    };

    const handleServicesClose = () => {
        setAnchorElServices(null);
    };

    const handleProfileClick = (event) => {
        setAnchorElProfile(event.currentTarget);
    };

    const handleProfileClose = () => {
        setAnchorElProfile(null);
    };

    const handleProfileOpen = () => {
        onProfileClick();
        handleProfileClose();
    };

    const handleLogoutClick = () => {
        onLogout();
        handleProfileClose();
    };

    const getPhotoUrl = () =>
        user?.has_photo ? `http://localhost:8000/users/${user.id}/photo?t=${Date.now()}` : undefined;

    return (
        <AppBar
            position="static"
            color="transparent"
            elevation={0}
            sx={{ borderBottom: '1px solid #f0f0f0' }}
        >
            <Container maxWidth={false} sx={{ px: { xs: 2, md: 4 } }}>
                <Toolbar disableGutters>
                    {/* Logo and Brand */}
                    <Link
                        href="/"
                        sx={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center' }}
                    >
                        <Stack direction="row" alignItems="center" spacing={1.5}>
                            <Box
                                component="img"
                                sx={{ height: 40, width: 'auto' }}
                                alt="RiskWatch Logo"
                                src="/riskwatch_logo.png"
                            />
                            <Typography
                                variant="h6"
                                component="div"
                                sx={{ fontWeight: 'bold', display: { xs: 'none', sm: 'block' } }}
                            >
                                RiskWatch
                            </Typography>
                        </Stack>
                    </Link>

                    <Box sx={{ flexGrow: 1 }} />

                    {user ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {/* Chat Icon */}
                            <Button
                                color="inherit"
                                startIcon={<ForumIcon />}
                                onClick={() => navigate('/chat')}
                                sx={{ textTransform: 'none', fontWeight: 'bold' }}
                            >
                                 Chat
                            </Button>

                            {/* Services Dropdown */}
                            <Button
                                color="inherit"
                                onClick={handleServicesClick}
                                sx={{ textTransform: 'none', fontWeight: 'bold' }}
                            >
                                Services
                            </Button>
                            <Menu
                                anchorEl={anchorElServices}
                                open={isServicesOpen}
                                onClose={handleServicesClose}
                                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                            >
                                <MenuItem component={RouterLink} to="/create-post" onClick={handleServicesClose}>Post</MenuItem>
                                <MenuItem component={RouterLink} to="/my-posts" onClick={handleServicesClose}>My Posts</MenuItem>
                                {user.role === 'admin' && [
                                    <Divider key="admin-divider" />,
                                    <MenuItem
                                        key="admin-link"
                                        component={RouterLink}
                                        to="/admin"
                                        onClick={handleServicesClose}
                                    >
                                        Admin
                                    </MenuItem>
                                ]}
                            </Menu>

                            {/* Avatar Dropdown Menu */}
                            <IconButton onClick={handleProfileClick} sx={{ p: 0 }}>
                                <Avatar
                                    sx={{ bgcolor: 'primary.main', color: 'primary.contrastText' }}
                                    src={getPhotoUrl()}
                                >
                                    {!user.has_photo && user.name.charAt(0).toUpperCase()}
                                </Avatar>
                            </IconButton>
                            <Menu
                                anchorEl={anchorElProfile}
                                open={isProfileOpen}
                                onClose={handleProfileClose}
                                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                            >
                                <MenuItem onClick={handleProfileOpen}>
                                    <PersonIcon fontSize="small" sx={{ mr: 1 }} />
                                    Profile
                                </MenuItem>
                                <MenuItem onClick={handleLogoutClick}>
                                    <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
                                    Logout
                                </MenuItem>
                            </Menu>
                        </Box>
                    ) : (
                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={onRegisterClick}
                                sx={{ borderRadius: '20px', textTransform: 'none', fontWeight: 'bold' }}
                            >
                                Register
                            </Button>
                            <Button
                                variant="outlined"
                                color="primary"
                                onClick={onLoginClick}
                                sx={{ borderRadius: '20px', textTransform: 'none', fontWeight: 'bold' }}
                            >
                                Login
                            </Button>
                        </Box>
                    )}
                </Toolbar>
            </Container>
        </AppBar>
    );
};

export default Navbar;
