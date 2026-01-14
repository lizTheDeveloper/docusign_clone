# Document Management Frontend

Complete React + TypeScript implementation for document management with upload, viewing, and management capabilities.

## Architecture

### Component Structure
```
src/
├── types/
│   └── document.ts          # TypeScript interfaces
├── services/
│   └── document.service.ts  # API client
├── components/
│   └── documents/
│       ├── DocumentUpload.tsx   # Upload with drag & drop
│       ├── DocumentList.tsx     # Document grid with pagination
│       ├── DocumentCard.tsx     # Individual document card
│       ├── DocumentViewer.tsx   # Document detail view
│       └── index.ts            # Barrel export
└── pages/
    └── Documents.tsx        # Main documents page
```

## Features

### DocumentUpload Component
- **Drag & Drop**: Intuitive file upload with visual feedback
- **File Validation**: Client-side checks for type (PDF only) and size (50MB max)
- **Custom Naming**: Optional custom document names
- **Progress Display**: Visual upload progress indicator
- **Error Handling**: Clear error messages for validation failures

### DocumentList Component
- **Pagination**: Navigate through large document collections (12 per page)
- **Search**: Real-time search across document names
- **Sorting**: Sort by upload date, name, or file size (ascending/descending)
- **Grid Layout**: Responsive grid (1-4 columns based on screen size)
- **Empty State**: Helpful message when no documents exist

### DocumentCard Component
- **Thumbnail Preview**: Shows document thumbnail or fallback icon
- **Metadata Display**: Name, page count, file size, upload date
- **Quick Actions**: Download and delete buttons with confirmation
- **Click to View**: Open document viewer on card click

### DocumentViewer Component
- **Full Metadata**: Complete document details and uploader info
- **PDF Preview**: Embedded PDF viewer with presigned URL
- **Page Thumbnails**: Grid of all page thumbnails
- **Processing Status**: Real-time status for processing/failed documents
- **Download**: Direct download button
- **Security**: Displays SHA-256 checksum for verification

### Documents Page
- **View Modes**: Toggle between list, upload, and viewer modes
- **Notifications**: Success/error toasts with auto-dismiss
- **Responsive**: Mobile-friendly layouts
- **Navigation**: Clean header with mode switching

## API Integration

### Service Layer (`document.service.ts`)
All API calls use the shared `api` client from `lib/api.ts` which handles:
- Base URL configuration
- Authentication headers
- Token refresh logic
- Error handling

#### Methods
```typescript
DocumentService.uploadDocument(file, name?)     // POST /documents
DocumentService.getDocument(documentId)          // GET /documents/:id
DocumentService.listDocuments(params?)           // GET /documents
DocumentService.downloadDocument(documentId)     // GET /documents/:id/download
DocumentService.getPreviewUrl(documentId)        // GET /documents/:id/preview
DocumentService.deleteDocument(documentId)       // DELETE /documents/:id
```

#### Utility Methods
```typescript
DocumentService.formatFileSize(bytes)            // Format bytes to KB/MB/GB
DocumentService.formatRelativeTime(dateString)   // Format to "X minutes ago"
```

## Type Definitions (`types/document.ts`)

### Core Types
```typescript
enum DocumentStatus {
    PROCESSING = 'processing',
    READY = 'ready',
    FAILED = 'failed',
}

interface Document {
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

interface DocumentMetadata extends Document {
    uploadedBy: {
        userId: string;
        name: string;
        email: string;
    };
    pages: DocumentPage[];
}
```

## Usage

### Basic Integration
```tsx
import { Documents } from '@/pages/Documents';

// Add to router
<Route path="/documents" element={<Documents />} />
```

### Individual Components
```tsx
import { DocumentUpload, DocumentList, DocumentViewer } from '@/components/documents';

// Upload
<DocumentUpload 
    onUploadComplete={(doc) => console.log('Uploaded:', doc)}
    onError={(err) => console.error(err)}
/>

// List
<DocumentList 
    onDocumentClick={(id) => navigate(`/documents/${id}`)}
    refreshTrigger={counter}
/>

// Viewer
<DocumentViewer 
    documentId={docId}
    onClose={() => navigate('/documents')}
/>
```

## Styling

Uses **Tailwind CSS** for all styling:
- Consistent spacing and colors
- Responsive breakpoints (sm, md, lg, xl)
- Hover and focus states
- Transitions and animations
- Accessible design patterns

## Error Handling

### Client-Side Validation
- File type: PDF only
- File size: 50MB maximum
- Empty file check
- Network errors

### Server-Side Errors
All API errors are caught and displayed to users with:
- Contextual error messages
- Auto-dismissing notifications
- Confirmation dialogs for destructive actions

## State Management

### Local Component State
- Upload progress
- Selected files
- View modes
- Loading states
- Error states

### Props-Based Communication
- Parent → Child: Configuration and callbacks
- Child → Parent: Events (upload complete, delete, etc.)
- Refresh triggers for list updates

## Performance Optimizations

1. **Pagination**: Only 12 documents loaded at a time
2. **Lazy Loading**: Components only render when needed
3. **Debounced Search**: Prevents excessive API calls
4. **Presigned URLs**: Direct S3 access for downloads/previews
5. **Image Optimization**: Thumbnails instead of full documents

## Security Features

1. **Authentication Required**: All routes protected by `ProtectedRoute`
2. **Token Management**: Automatic token refresh via axios interceptors
3. **HTTPS**: Production uses secure connections
4. **Presigned URLs**: Time-limited access to documents
5. **Input Validation**: Client-side validation before upload

## Future Enhancements

- [ ] Bulk operations (select multiple, delete multiple)
- [ ] Advanced filters (date range, file size range)
- [ ] Document sharing with other users
- [ ] Document versioning UI
- [ ] Folder/tag organization
- [ ] Batch upload support
- [ ] Real-time upload progress using WebSockets
- [ ] Document annotations/comments
- [ ] Print preview
- [ ] Export to different formats

## Testing

### Manual Testing Checklist
- [ ] Upload valid PDF
- [ ] Upload invalid file type (error)
- [ ] Upload oversized file (error)
- [ ] Drag and drop upload
- [ ] List documents with pagination
- [ ] Search documents
- [ ] Sort documents (all options)
- [ ] View document details
- [ ] Download document
- [ ] Delete document (with confirmation)
- [ ] Processing status display
- [ ] Error states (network, server errors)
- [ ] Responsive design (mobile, tablet, desktop)

### Integration Testing
Ensure backend API is running:
```bash
cd backend
uvicorn app.main:app --reload
```

Start frontend dev server:
```bash
cd frontend
npm run dev
```

Navigate to: http://localhost:5173/documents

## Troubleshooting

### Upload Fails
1. Check file is valid PDF
2. Check file size < 50MB
3. Verify backend is running
4. Check S3 credentials in backend .env
5. Check browser console for errors

### Preview Not Loading
1. Verify document status is "ready"
2. Check presigned URL expiration
3. Verify S3 bucket CORS settings
4. Check browser console for CORS errors

### Authentication Issues
1. Verify token is stored in localStorage
2. Check token hasn't expired
3. Try logging out and back in
4. Check API base URL configuration

## API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/documents` | Upload document |
| GET | `/api/v1/documents` | List user's documents |
| GET | `/api/v1/documents/:id` | Get document metadata |
| GET | `/api/v1/documents/:id/download` | Download document |
| GET | `/api/v1/documents/:id/preview` | Get preview URL |
| DELETE | `/api/v1/documents/:id` | Delete document |

## Dependencies

### Required
- `react` - UI framework
- `react-router-dom` - Routing
- `axios` - HTTP client (configured in `lib/api.ts`)
- `tailwindcss` - Styling

### Backend Requirements
- FastAPI backend running on http://localhost:8000
- S3 storage configured
- Authentication endpoints available
- CORS enabled for frontend origin
