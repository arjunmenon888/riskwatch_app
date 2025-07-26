// frontend/src/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('riskwatch_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- NEW CHAT API FUNCTIONS ---

/**
 * Searches for users by their email address.
 * @param {string} query - The search term.
 * @returns {Promise<Array<{email: string, name: string}>>}
 */
export const searchUsers = async (query) => {
  if (!query) return []; // Don't search for an empty string
  const response = await api.get(`/chat/users/search?query=${query}`);
  return response.data;
};

/**
 * Creates a new chat room with a recipient or gets the existing one.
 * @param {string} recipientEmail - The email of the user to chat with.
 * @returns {Promise<Object>} The chat room object.
 */
export const startChat = async (recipientEmail) => {
  const response = await api.post('/chat/rooms', { recipient_email: recipientEmail });
  return response.data;
};

// --- END OF NEW FUNCTIONS ---

export default api;