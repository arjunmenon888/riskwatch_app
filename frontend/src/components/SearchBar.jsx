// frontend/src/components/SearchBar.jsx
import React, { useState } from 'react';
import { TextField, InputAdornment } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useDebounce } from 'use-debounce';

const SearchBar = ({ onSearchChange }) => {
    const [text, setText] = useState('');
    
    // Debounce hook: waits for the user to stop typing for 300ms before calling onSearchChange
    // This prevents API calls on every single keystroke.
    const [debouncedValue] = useDebounce(text, 300);

    // useEffect to call the parent component's search handler when debounced value changes
    React.useEffect(() => {
        onSearchChange(debouncedValue);
    }, [debouncedValue, onSearchChange]);

    return (
        <TextField
            variant="outlined"
            placeholder="Search posts..."
            onChange={(e) => setText(e.target.value)}
            fullWidth
            sx={{
                // Set a max-width for larger screens
                maxWidth: { sm: 400 },
                '& .MuiOutlinedInput-root': {
                    borderRadius: '12px', // Softer rounded corners
                },
            }}
            InputProps={{
                startAdornment: (
                    <InputAdornment position="start">
                        <SearchIcon />
                    </InputAdornment>
                ),
            }}
        />
    );
};

export default SearchBar;