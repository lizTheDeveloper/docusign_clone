/**
 * Document types and interfaces
 */

export enum DocumentStatus {
    PROCESSING = 'processing',
    READY = 'ready',
    FAILED = 'failed',
}

export interface Document {
    documentId: string;
    name: string;
    originalFilename: string;
    fileType: string;
    fileSize: number;
    pageCount: number;
    status: DocumentStatus;
    thumbnailUrl?: string;
    checksum: string;
    uploadedAt: string;
}

export interface DocumentPage {
    pageNumber: number;
    width: number;
    height: number;
    thumbnailUrl?: string;
}

export interface DocumentMetadata extends Document {
    uploadedBy: {
        userId: string;
        name: string;
        email: string;
    };
    pages: DocumentPage[];
}

export interface DocumentListItem {
    documentId: string;
    name: string;
    fileSize: number;
    pageCount: number;
    uploadedAt: string;
    thumbnailUrl?: string;
}

export interface Pagination {
    page: number;
    limit: number;
    totalPages: number;
    totalItems: number;
}

export interface DocumentListResponse {
    documents: DocumentListItem[];
    pagination: Pagination;
}

export interface DocumentUploadRequest {
    file: File;
    name?: string;
}

export interface PreviewUrlResponse {
    previewUrl: string;
    expiresAt: string;
}
