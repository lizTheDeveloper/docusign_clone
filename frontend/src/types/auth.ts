/**
 * Authentication types and interfaces
 */

export interface User {
    id: string;
    email: string;
    name: string;
    phone?: string;
    email_verified: boolean;
    created_at: string;
    updated_at: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}

export interface RegisterRequest {
    email: string;
    password: string;
    name: string;
    phone?: string;
}

export interface RegisterResponse {
    user: User;
    message: string;
}

export interface ForgotPasswordRequest {
    email: string;
}

export interface ResetPasswordRequest {
    token: string;
    new_password: string;
}

export interface UpdateProfileRequest {
    name?: string;
    phone?: string;
}

export interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => void;
    refreshToken: () => Promise<void>;
    updateProfile: (data: UpdateProfileRequest) => Promise<void>;
}

export interface ApiError {
    detail: string;
    status_code?: number;
}
