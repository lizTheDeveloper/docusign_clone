/**
 * DocumentViewer component - displays document metadata and pages
 */
import React, { useState, useEffect } from 'react';
import { DocumentService } from '../../services/document.service';
import { DocumentMetadata, DocumentStatus } from '../../types/document';

interface DocumentViewerProps {
    documentId: string;
    onClose?: () => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
    documentId,
    onClose,
}) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [document, setDocument] = useState<DocumentMetadata | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);

    useEffect(() => {
        loadDocument();
    }, [documentId]);

    const loadDocument = async () => {
        setLoading(true);
        setError(null);
        try {
            const doc = await DocumentService.getDocument(documentId);
            setDocument(doc);

            // Load preview URL if document is ready
            if (doc.status === DocumentStatus.READY) {
                const preview = await DocumentService.getPreviewUrl(documentId);
                setPreviewUrl(preview.previewUrl);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load document');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
        try {
            await DocumentService.downloadDocument(documentId);
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to download document');
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error || !document) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                {error || 'Document not found'}
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-lg max-w-6xl mx-auto">
            {/* Header */}
            <div className="border-b border-gray-200 p-6 flex items-start justify-between">
                <div className="flex-1">
                    <h2 className="text-2xl font-bold text-gray-900">{document.name}</h2>
                    <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-600">
                        <span>{document.pageCount} pages</span>
                        <span>•</span>
                        <span>{DocumentService.formatFileSize(document.fileSize)}</span>
                        <span>•</span>
                        <span>
                            Uploaded {DocumentService.formatRelativeTime(document.uploadedAt)}
                        </span>
                        {document.status === DocumentStatus.PROCESSING && (
                            <>
                                <span>•</span>
                                <span className="text-yellow-600 font-medium">Processing...</span>
                            </>
                        )}
                        {document.status === DocumentStatus.FAILED && (
                            <>
                                <span>•</span>
                                <span className="text-red-600 font-medium">Processing Failed</span>
                            </>
                        )}
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleDownload}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        Download
                    </button>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                        >
                            Close
                        </button>
                    )}
                </div>
            </div>

            {/* Document metadata */}
            <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Details</h3>
                <dl className="grid grid-cols-2 gap-4">
                    <div>
                        <dt className="text-sm font-medium text-gray-500">Original Filename</dt>
                        <dd className="mt-1 text-sm text-gray-900">
                            {document.originalFilename}
                        </dd>
                    </div>
                    <div>
                        <dt className="text-sm font-medium text-gray-500">File Type</dt>
                        <dd className="mt-1 text-sm text-gray-900">{document.fileType}</dd>
                    </div>
                    <div>
                        <dt className="text-sm font-medium text-gray-500">Uploaded By</dt>
                        <dd className="mt-1 text-sm text-gray-900">
                            {document.uploadedBy.name} ({document.uploadedBy.email})
                        </dd>
                    </div>
                    <div>
                        <dt className="text-sm font-medium text-gray-500">Checksum (SHA-256)</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono truncate">
                            {document.checksum}
                        </dd>
                    </div>
                </dl>
            </div>

            {/* Preview / Pages */}
            <div className="p-6">
                {document.status === DocumentStatus.READY && previewUrl ? (
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Preview</h3>
                        <div className="bg-gray-100 rounded-lg overflow-hidden">
                            <iframe
                                src={previewUrl}
                                className="w-full h-[600px]"
                                title="Document Preview"
                            />
                        </div>
                    </div>
                ) : document.status === DocumentStatus.PROCESSING ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Processing document...</p>
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <p className="text-gray-600">Preview not available</p>
                    </div>
                )}

                {/* Page thumbnails */}
                {document.pages && document.pages.length > 0 && (
                    <div className="mt-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Pages</h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                            {document.pages.map((page) => (
                                <div
                                    key={page.pageNumber}
                                    className="border border-gray-200 rounded-lg overflow-hidden"
                                >
                                    {page.thumbnailUrl ? (
                                        <img
                                            src={page.thumbnailUrl}
                                            alt={`Page ${page.pageNumber}`}
                                            className="w-full h-auto"
                                        />
                                    ) : (
                                        <div className="bg-gray-100 aspect-[8.5/11] flex items-center justify-center">
                                            <span className="text-gray-400">
                                                Page {page.pageNumber}
                                            </span>
                                        </div>
                                    )}
                                    <div className="p-2 text-center text-xs text-gray-600">
                                        Page {page.pageNumber}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
