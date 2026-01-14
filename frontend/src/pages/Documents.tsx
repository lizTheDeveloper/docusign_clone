/**
 * Documents page - main page for document management
 */
import React, { useState } from 'react';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { DocumentList } from '../components/documents/DocumentList';
import { DocumentViewer } from '../components/documents/DocumentViewer';
import { Document } from '../types/document';

type ViewMode = 'list' | 'upload' | 'viewer';

export const Documents: React.FC = () => {
    const [viewMode, setViewMode] = useState<ViewMode>('list');
    const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleUploadComplete = (document: Document) => {
        setSuccessMessage(`Document "${document.name}" uploaded successfully!`);
        setRefreshTrigger((prev) => prev + 1);
        setViewMode('list');

        // Clear success message after 5 seconds
        setTimeout(() => setSuccessMessage(null), 5000);
    };

    const handleUploadError = (error: string) => {
        setErrorMessage(error);
        setTimeout(() => setErrorMessage(null), 5000);
    };

    const handleDocumentClick = (documentId: string) => {
        setSelectedDocumentId(documentId);
        setViewMode('viewer');
    };

    const handleCloseViewer = () => {
        setSelectedDocumentId(null);
        setViewMode('list');
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center justify-between">
                        <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setViewMode('list')}
                                className={`px-4 py-2 rounded-md transition-colors ${
                                    viewMode === 'list'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                                }`}
                            >
                                My Documents
                            </button>
                            <button
                                onClick={() => setViewMode('upload')}
                                className={`px-4 py-2 rounded-md transition-colors ${
                                    viewMode === 'upload'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                                }`}
                            >
                                Upload
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Notifications */}
            {successMessage && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
                        <div className="flex items-center">
                            <svg
                                className="h-5 w-5 text-green-600 mr-2"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                    clipRule="evenodd"
                                />
                            </svg>
                            <span className="text-green-800">{successMessage}</span>
                        </div>
                        <button
                            onClick={() => setSuccessMessage(null)}
                            className="text-green-600 hover:text-green-800"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {errorMessage && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
                        <div className="flex items-center">
                            <svg
                                className="h-5 w-5 text-red-600 mr-2"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                    clipRule="evenodd"
                                />
                            </svg>
                            <span className="text-red-800">{errorMessage}</span>
                        </div>
                        <button
                            onClick={() => setErrorMessage(null)}
                            className="text-red-600 hover:text-red-800"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {viewMode === 'upload' && (
                    <DocumentUpload
                        onUploadComplete={handleUploadComplete}
                        onError={handleUploadError}
                    />
                )}

                {viewMode === 'list' && (
                    <DocumentList
                        onDocumentClick={handleDocumentClick}
                        refreshTrigger={refreshTrigger}
                    />
                )}

                {viewMode === 'viewer' && selectedDocumentId && (
                    <DocumentViewer
                        documentId={selectedDocumentId}
                        onClose={handleCloseViewer}
                    />
                )}
            </div>
        </div>
    );
};
