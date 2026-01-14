/**
 * Authentication context provider
 * Manages authentication state and provides auth methods to the app
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '@/services/auth.service';
import type { User, AuthContextType, RegisterRequest, UpdateProfileRequest } from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Load user on mount if token exists
    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem('access_token');

            if (token) {
                try {
                    const userData = await authService.getCurrentUser();
                    setUser(userData);
                } catch (error) {
                    // Token invalid, clear storage
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                }
            }

            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = useCallback(async (email: string, password: string) => {
        const response = await authService.login({ email, password });
        setUser(response.user);
    }, []);

    const register = useCallback(async (data: RegisterRequest) => {
        const response = await authService.register(data);
        // Note: User needs to verify email before they can login
        // So we don't auto-login here
    }, []);

    const logout = useCallback(() => {
        authService.logout();
        setUser(null);
    }, []);

    const refreshToken = useCallback(async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await authService.refreshToken(refreshToken);
        setUser(response.user);
    }, []);

    const updateProfile = useCallback(async (data: UpdateProfileRequest) => {
        const updatedUser = await authService.updateProfile(data);
        setUser(updatedUser);
    }, []);

    const value: AuthContextType = {
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshToken,
        updateProfile,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
