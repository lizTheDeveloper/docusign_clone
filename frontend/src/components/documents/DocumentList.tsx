/**
 * DocumentList component - displays user's documents with pagination
 */
import React, { useState, useEffect } from 'react';
import { DocumentService } from '../../services/document.service';
import { DocumentListItem, DocumentListResponse } from '../../types/document';
import { DocumentCard } from './DocumentCard';

interface DocumentListProps {
    onDocumentClick?: (documentId: string) => void;
    refreshTrigger?: number;
}

export const DocumentList: React.FC<DocumentListProps> = ({
    onDocumentClick,
    refreshTrigger = 0,
}) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<DocumentListResponse | null>(null);
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<string>('uploadedAt');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
    const [search, setSearch] = useState('');

    useEffect(() => {
        loadDocuments();
    }, [page, sortBy, sortOrder, search, refreshTrigger]);

    const loadDocuments = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await DocumentService.listDocuments({
                page,
                limit: 12,
                sortBy,
                sortOrder,
                search: search || undefined,
            });
            setData(response);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load documents');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (documentId: string) => {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            await DocumentService.deleteDocument(documentId);
            loadDocuments(); // Refresh list
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to delete document');
        }
    };

    const handleDownload = async (documentId: string) => {
        try {
            await DocumentService.downloadDocument(documentId);
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to download document');
        }
    };

    if (loading && !data) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error && !data) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                {error}
            </div>
        );
    }

    if (!data?.documents.length) {
        return (
            <div className="text-center py-12">
                <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
                <p className="mt-1 text-sm text-gray-500">
                    Get started by uploading a document.
                </p>
            </div>
        );
    }

    return (
        <div>
            {/* Search and filters */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                    <input
                        type="text"
                        placeholder="Search documents..."
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1); // Reset to first page on search
                        }}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>
                <div className="flex gap-2">
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="uploadedAt">Upload Date</option>
                        <option value="name">Name</option>
                        <option value="fileSize">Size</option>
                    </select>
                    <button
                        onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
                    >
                        {sortOrder === 'asc' ? '↑' : '↓'}
                    </button>
                </div>
            </div>

            {/* Document grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {data.documents.map((doc) => (
                    <DocumentCard
                        key={doc.documentId}
                        document={doc}
                        onClick={() => onDocumentClick?.(doc.documentId)}
                        onDelete={() => handleDelete(doc.documentId)}
                        onDownload={() => handleDownload(doc.documentId)}
                    />
                ))}
            </div>

            {/* Pagination */}
            {data.pagination.totalPages > 1 && (
                <div className="mt-6 flex justify-center items-center gap-2">
                    <button
                        onClick={() => setPage(page - 1)}
                        disabled={page === 1 || loading}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Previous
                    </button>
                    <span className="text-sm text-gray-600">
                        Page {page} of {data.pagination.totalPages}
                    </span>
                    <button
                        onClick={() => setPage(page + 1)}
                        disabled={page === data.pagination.totalPages || loading}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
};
