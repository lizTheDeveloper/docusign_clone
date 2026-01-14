/**
 * Authentication service - handles all auth-related API calls
 */
import api from '@/lib/api';
import type {
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    User,
} from '@/types/auth';

export const authService = {
    /**
     * Register a new user
     */
    async register(data: RegisterRequest): Promise<RegisterResponse> {
        const response = await api.post<RegisterResponse>('/auth/register', data);
        return response.data;
    },

    /**
     * Login with email and password
     */
    async login(data: LoginRequest): Promise<LoginResponse> {
        const response = await api.post<LoginResponse>('/auth/login', data);

        // Store tokens in localStorage
        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
        }

        return response.data;
    },

    /**
     * Logout the current user
     */
    async logout(): Promise<void> {
        try {
            await api.post('/auth/logout');
        } finally {
            // Clear tokens regardless of API response
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    },

    /**
     * Refresh the access token
     */
    async refreshToken(refreshToken: string): Promise<LoginResponse> {
        const response = await api.post<LoginResponse>('/auth/refresh-token', {
            refresh_token: refreshToken,
        });

        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
        }

        return response.data;
    },

    /**
     * Get current user profile
     */
    async getCurrentUser(): Promise<User> {
        const response = await api.get<User>('/auth/me');
        return response.data;
    },

    /**
     * Update current user profile
     */
    async updateProfile(data: UpdateProfileRequest): Promise<User> {
        const response = await api.patch<User>('/auth/me', data);
        return response.data;
    },

    /**
     * Verify email with token
     */
    async verifyEmail(token: string): Promise<{ message: string }> {
        const response = await api.post<{ message: string }>('/auth/verify-email', { token });
        return response.data;
    },

    /**
     * Resend email verification
     */
    async resendVerification(email: string): Promise<{ message: string }> {
        const response = await api.post<{ message: string }>('/auth/resend-verification', { email });
        return response.data;
    },

    /**
     * Request password reset
     */
    async forgotPassword(data: ForgotPasswordRequest): Promise<{ message: string }> {
        const response = await api.post<{ message: string }>('/auth/forgot-password', data);
        return response.data;
    },

    /**
     * Reset password with token
     */
    async resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
        const response = await api.post<{ message: string }>('/auth/reset-password', data);
        return response.data;
    },
};
