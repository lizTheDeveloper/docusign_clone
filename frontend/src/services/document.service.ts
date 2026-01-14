/**
 * Document service API client
 */
import { api } from '../lib/api';
import {
    Document,
    DocumentListResponse,
    DocumentMetadata,
    PreviewUrlResponse,
} from '../types/document';

export class DocumentService {
    /**
     * Upload a document
     */
    static async uploadDocument(file: File, name?: string): Promise<Document> {
        const formData = new FormData();
        formData.append('file', file);
        if (name) {
            formData.append('name', name);
        }

        const response = await api.post<Document>('/documents', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        return response.data;
    }

    /**
     * Get document metadata
     */
    static async getDocument(documentId: string): Promise<DocumentMetadata> {
        const response = await api.get<DocumentMetadata>(`/documents/${documentId}`);
        return response.data;
    }

    /**
     * List user's documents
     */
    static async listDocuments(params?: {
        page?: number;
        limit?: number;
        sortBy?: string;
        sortOrder?: 'asc' | 'desc';
        search?: string;
    }): Promise<DocumentListResponse> {
        const response = await api.get<DocumentListResponse>('/documents', {
            params,
        });
        return response.data;
    }

    /**
     * Download document
     */
    static async downloadDocument(documentId: string): Promise<void> {
        // Backend returns a redirect to presigned URL
        const response = await api.get(`/documents/${documentId}/download`, {
            responseType: 'blob',
            maxRedirects: 5,
        });

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `document-${documentId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    }

    /**
     * Get preview URL for document
     */
    static async getPreviewUrl(documentId: string): Promise<PreviewUrlResponse> {
        const response = await api.get<PreviewUrlResponse>(
            `/documents/${documentId}/preview`
        );
        return response.data;
    }

    /**
     * Delete document
     */
    static async deleteDocument(documentId: string): Promise<void> {
        await api.delete(`/documents/${documentId}`);
    }

    /**
     * Format file size to human readable format
     */
    static formatFileSize(bytes: number): string {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Format date to relative time
     */
    static formatRelativeTime(dateString: string): string {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

        return date.toLocaleDateString();
    }
}
