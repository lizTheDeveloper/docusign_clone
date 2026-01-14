/**
 * DocumentCard component - displays a single document in the list
 */
import React from 'react';
import { DocumentListItem } from '../../types/document';
import { DocumentService } from '../../services/document.service';

interface DocumentCardProps {
    document: DocumentListItem;
    onClick?: () => void;
    onDelete?: () => void;
    onDownload?: () => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
    document,
    onClick,
    onDelete,
    onDownload,
}) => {
    const handleAction = (e: React.MouseEvent, action: () => void) => {
        e.stopPropagation();
        action();
    };

    return (
        <div
            onClick={onClick}
            className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 overflow-hidden"
        >
            {/* Thumbnail */}
            <div className="h-48 bg-gray-100 flex items-center justify-center">
                {document.thumbnailUrl ? (
                    <img
                        src={document.thumbnailUrl}
                        alt={document.name}
                        className="max-h-full max-w-full object-contain"
                    />
                ) : (
                    <svg
                        className="h-16 w-16 text-gray-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                    >
                        <path
                            fillRule="evenodd"
                            d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                            clipRule="evenodd"
                        />
                    </svg>
                )}
            </div>

            {/* Content */}
            <div className="p-4">
                <h3 className="font-medium text-gray-900 truncate" title={document.name}>
                    {document.name}
                </h3>
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                    <span>{document.pageCount} pages</span>
                    <span>{DocumentService.formatFileSize(document.fileSize)}</span>
                </div>
                <div className="mt-1 text-xs text-gray-500">
                    {DocumentService.formatRelativeTime(document.uploadedAt)}
                </div>

                {/* Actions */}
                <div className="mt-4 flex gap-2">
                    <button
                        onClick={(e) => handleAction(e, onDownload!)}
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        title="Download"
                    >
                        <svg
                            className="h-4 w-4 mx-auto"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                        </svg>
                    </button>
                    <button
                        onClick={(e) => handleAction(e, onDelete!)}
                        className="flex-1 px-3 py-2 text-sm border border-red-300 text-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
                        title="Delete"
                    >
                        <svg
                            className="h-4 w-4 mx-auto"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
};
