import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface User {
    id: string;
    email: string;
    full_name?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => void;
    recover: (email: string) => Promise<void>;
    updatePassword: (currentPassword: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [isLoading, setIsLoading] = useState(true);

    // Configure axios defaults
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            localStorage.setItem('token', token);
        } else {
            delete axios.defaults.headers.common['Authorization'];
            localStorage.removeItem('token');
        }
    }, [token]);

    // Check auth status on load
    useEffect(() => {
        const checkAuth = async () => {
            if (!token) {
                setIsLoading(false);
                return;
            }
            try {
                const res = await axios.get('/auth/me');
                // Since we didn't setup a proxy for /auth separately, we should make sure the paths align.
                // Assuming /api/auth or just /auth. My backend defined /auth/me. 
                // Vite proxy usually forwards /api to backend. I should check vite config.
                // If my backend uses /auth, I might need to adjust proxy or backend prefix.
                // For now let's assume /auth is proxied or I'll fix it.
                setUser(res.data);
            } catch (err) {
                logout();
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [token]);

    const login = async (email: string, password: string) => {
        // Send JSON payload
        const res = await axios.post('/auth/login', {
            username: email,
            password: password
        });
        setToken(res.data.access_token);
        // Fetch user immediately
        const userRes = await axios.get('/auth/me', {
            headers: { Authorization: `Bearer ${res.data.access_token}` }
        });
        setUser(userRes.data);
    };

    const register = async (email: string, password: string, full_name?: string) => {
        await axios.post('/auth/register', { email, password, full_name });
        await login(email, password);
    };

    const recover = async (email: string) => {
        await axios.post('/auth/recover', { email });
    };

    const updatePassword = async (currentPassword: string, newPassword: string) => {
        await axios.put('/auth/password', {
            current_password: currentPassword,
            new_password: newPassword
        });
    };

    const logout = () => {
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, recover, updatePassword }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
