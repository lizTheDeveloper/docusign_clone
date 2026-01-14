/**
 * Email verification handler component
 */
import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { authService } from '@/services/auth.service';
import type { ApiError } from '@/types/auth';
import { AxiosError } from 'axios';

export const VerifyEmail: React.FC = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');

    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState<string>('');

    useEffect(() => {
        const verifyEmail = async () => {
            if (!token) {
                setStatus('error');
                setMessage('Invalid or missing verification token.');
                return;
            }

            try {
                const response = await authService.verifyEmail(token);
                setStatus('success');
                setMessage(response.message || 'Email verified successfully!');
            } catch (err) {
                const axiosError = err as AxiosError<ApiError>;
                setStatus('error');
                setMessage(
                    axiosError.response?.data?.detail ||
                    'Failed to verify email. The link may have expired.'
                );
            }
        };

        verifyEmail();
    }, [token]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full">
                {status === 'loading' && (
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Verifying your email...</p>
                    </div>
                )}

                {status === 'success' && (
                    <div className="rounded-md bg-green-50 p-4">
                        <div className="flex">
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-green-800">
                                    Email verified successfully!
                                </h3>
                                <div className="mt-2 text-sm text-green-700">
                                    <p>{message}</p>
                                    <p className="mt-4">
                                        <Link
                                            to="/login"
                                            className="font-medium text-green-600 hover:text-green-500 underline"
                                        >
                                            Continue to login →
                                        </Link>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {status === 'error' && (
                    <div className="rounded-md bg-red-50 p-4">
                        <div className="flex">
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-red-800">
                                    Verification failed
                                </h3>
                                <div className="mt-2 text-sm text-red-700">
                                    <p>{message}</p>
                                    <div className="mt-4 space-y-2">
                                        <p>
                                            <Link
                                                to="/login"
                                                className="font-medium text-red-600 hover:text-red-500 underline"
                                            >
                                                Try logging in →
                                            </Link>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
