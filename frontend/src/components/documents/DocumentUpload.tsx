/**
 * DocumentUpload component - handles file upload with drag & drop
 */
import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { DocumentService } from '../../services/document.service';
import { Document as DocumentType } from '../../types/document';

interface DocumentUploadProps {
    onUploadComplete?: (document: DocumentType) => void;
    onError?: (error: string) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
    onUploadComplete,
    onError,
}) => {
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [progress, setProgress] = useState(0);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [documentName, setDocumentName] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (file: File) => {
        // Validate file type
        if (file.type !== 'application/pdf') {
            onError?.('Only PDF files are allowed');
            return;
        }

        // Validate file size (50MB)
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            onError?.('File size must be less than 50MB');
            return;
        }

        setSelectedFile(file);
        setDocumentName(file.name.replace('.pdf', ''));
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setUploading(true);
        setProgress(0);

        // Simulate progress (real implementation would use upload progress)
        const progressInterval = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 90) {
                    clearInterval(progressInterval);
                    return 90;
                }
                return prev + 10;
            });
        }, 200);

        try {
            const document = await DocumentService.uploadDocument(
                selectedFile,
                documentName || undefined
            );

            setProgress(100);
            setTimeout(() => {
                onUploadComplete?.(document);
                resetForm();
            }, 500);
        } catch (error: any) {
            clearInterval(progressInterval);
            const message = error.response?.data?.detail || 'Failed to upload document';
            onError?.(message);
        } finally {
            clearInterval(progressInterval);
            setUploading(false);
        }
    };

    const resetForm = () => {
        setSelectedFile(null);
        setDocumentName('');
        setProgress(0);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="max-w-2xl mx-auto">
            {!selectedFile ? (
                <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                        dragActive
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 hover:border-gray-400'
                    }`}
                >
                    <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                        aria-hidden="true"
                    >
                        <path
                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                    <div className="mt-4">
                        <label htmlFor="file-upload" className="cursor-pointer">
                            <span className="text-blue-600 font-semibold hover:text-blue-700">
                                Click to upload
                            </span>
                            <span className="text-gray-600"> or drag and drop</span>
                            <input
                                ref={fileInputRef}
                                id="file-upload"
                                name="file-upload"
                                type="file"
                                accept=".pdf,application/pdf"
                                className="sr-only"
                                onChange={handleChange}
                            />
                        </label>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">PDF up to 50MB</p>
                </div>
            ) : (
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center">
                            <svg
                                className="h-10 w-10 text-red-500"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                                    clipRule="evenodd"
                                />
                            </svg>
                            <div className="ml-3">
                                <p className="text-sm font-medium text-gray-900">
                                    {selectedFile.name}
                                </p>
                                <p className="text-xs text-gray-500">
                                    {DocumentService.formatFileSize(selectedFile.size)}
                                </p>
                            </div>
                        </div>
                        {!uploading && (
                            <button
                                onClick={resetForm}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg
                                    className="h-5 w-5"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        )}
                    </div>

                    <div className="mb-4">
                        <label
                            htmlFor="document-name"
                            className="block text-sm font-medium text-gray-700 mb-1"
                        >
                            Document Name (optional)
                        </label>
                        <input
                            type="text"
                            id="document-name"
                            value={documentName}
                            onChange={(e) => setDocumentName(e.target.value)}
                            disabled={uploading}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                            placeholder="Enter custom name or leave blank to use filename"
                        />
                    </div>

                    {uploading && (
                        <div className="mb-4">
                            <div className="flex justify-between text-sm text-gray-600 mb-1">
                                <span>Uploading...</span>
                                <span>{progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${progress}%` }}
                                ></div>
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {uploading ? 'Uploading...' : 'Upload Document'}
                    </button>
                </div>
            )}
        </div>
    );
};
