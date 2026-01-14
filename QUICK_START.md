# Quick Start - Testing Document Management

Complete guide to test the document management system end-to-end.

## Prerequisites Checklist
- [ ] PostgreSQL 14+ running
- [ ] Python 3.12+ installed
- [ ] Node.js 18+ installed
- [ ] AWS S3 bucket created (or LocalStack for local dev)
- [ ] `.env` file configured in backend/

## Step 1: Backend Setup

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Configure Environment
Create `backend/.env` from `.env.example`:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/docusign_db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Run Migrations
```bash
alembic upgrade head
```

### Start Backend
```bash
uvicorn app.main:app --reload
```

✅ Backend running at: http://localhost:8000  
✅ API docs at: http://localhost:8000/docs

## Step 2: Frontend Setup

### Install Dependencies
```bash
cd frontend
npm install
```

### Verify Configuration
Check `src/lib/api.ts` has correct baseURL:
```typescript
baseURL: 'http://localhost:8000/api/v1'
```

### Start Frontend
```bash
npm run dev
```

✅ Frontend running at: http://localhost:5173

## Step 3: Create Test User

### Option 1: Via Frontend
1. Go to http://localhost:5173/register
2. Fill out registration form:
   - Name: Test User
   - Email: test@example.com
   - Password: TestPassword123
3. Check email for verification link (or check backend logs for token)
4. Verify email via link or API docs

### Option 2: Via API Docs
1. Go to http://localhost:8000/docs
2. POST `/api/v1/auth/register`
3. GET `/api/v1/auth/verify-email?token={token}`
4. POST `/api/v1/auth/login`

## Step 4: Test Document Upload

### Via Frontend UI
1. Login at http://localhost:5173/login
2. Click "Go to Documents" or navigate to /documents
3. Click "Upload" button
4. Drag & drop a PDF file or click to browse
5. Optionally enter custom name
6. Click "Upload Document"
7. Watch progress bar
8. See success notification
9. Document appears in list

### Test Cases
- ✅ Upload valid PDF (< 50MB)
- ❌ Upload non-PDF file (should error)
- ❌ Upload file > 50MB (should error)
- ✅ Upload without custom name (uses filename)
- ✅ Upload with custom name
- ✅ Drag & drop upload
- ✅ Click to browse upload

## Step 5: Test Document Listing

### Features to Test
- ✅ Documents display in grid
- ✅ Pagination works (if > 12 docs)
- ✅ Search by name
- ✅ Sort by upload date (default)
- ✅ Sort by name (A-Z and Z-A)
- ✅ Sort by size (small to large, large to small)
- ✅ Thumbnails display (or fallback icon)
- ✅ Metadata displays (name, pages, size, date)

### Expected Behavior
- Grid responsive (1 col mobile → 4 cols desktop)
- Empty state shows when no documents
- Loading spinner during fetch
- Error message if API fails

## Step 6: Test Document Viewer

### Open Document
1. Click on any document card
2. View opens with full metadata

### Features to Test
- ✅ Document name displays
- ✅ Metadata shows (pages, size, date)
- ✅ Uploader info displays
- ✅ PDF preview loads (if ready)
- ✅ Page thumbnails display
- ✅ Checksum visible
- ✅ Status indicator (processing/ready/failed)
- ✅ Download button works
- ✅ Close button returns to list

### Expected States
- **Processing**: Loading spinner, no preview
- **Ready**: Preview iframe, page thumbnails
- **Failed**: Error message, no preview

## Step 7: Test Download

### Via Document Card
1. In list view, click download icon on card
2. File downloads to default location

### Via Document Viewer
1. Open document
2. Click "Download" button
3. File downloads

### Verify
- ✅ File downloads as PDF
- ✅ Filename is meaningful
- ✅ File opens correctly in PDF viewer
- ✅ Content matches uploaded document

## Step 8: Test Delete

### Via Document Card
1. In list view, click delete icon (trash)
2. Confirm deletion in dialog
3. Document removed from list

### Verify
- ✅ Confirmation dialog appears
- ✅ Cancel button cancels operation
- ✅ Confirm button deletes document
- ✅ List refreshes automatically
- ✅ Document no longer appears

## Step 9: Test Error Scenarios

### Network Errors
- ✅ Stop backend → attempt operation → see error
- ✅ Invalid auth token → redirects to login
- ✅ Server error → user-friendly message

### Validation Errors
- ✅ Wrong file type → clear error message
- ✅ File too large → clear error message
- ✅ Empty file → handled gracefully

### Edge Cases
- ✅ Very long document name → truncates properly
- ✅ Document with many pages → all display
- ✅ Multiple rapid clicks → no duplicate operations

## Step 10: Test Responsive Design

### Mobile (320px - 640px)
- ✅ Upload area adapts
- ✅ Single column grid
- ✅ Actions stack vertically
- ✅ Viewer readable

### Tablet (641px - 1024px)
- ✅ 2-3 column grid
- ✅ Touch-friendly buttons
- ✅ Horizontal controls

### Desktop (1025px+)
- ✅ 4 column grid
- ✅ Hover states work
- ✅ All features accessible

## Troubleshooting

### Backend Issues

**Database connection fails**
```bash
# Check PostgreSQL is running
psql -U postgres -h localhost
# Verify DATABASE_URL in .env
```

**S3 upload fails**
```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name
# Check .env S3 configuration
```

**Alembic migration fails**
```bash
# Reset database
alembic downgrade base
alembic upgrade head
```

### Frontend Issues

**API calls fail (CORS)**
```bash
# Verify CORS_ORIGINS in backend .env includes frontend URL
CORS_ORIGINS=http://localhost:5173
```

**Authentication fails**
```bash
# Clear localStorage
localStorage.clear()
# Re-login
```

**Build fails**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Common Errors

**"Signature has expired" on preview**
- Presigned URLs expire after 1 hour
- Refresh the page to get new URL

**"Document not found"**
- Document may have been deleted
- Check documentId is correct
- Verify user has access

**"Network Error"**
- Backend not running
- Wrong API URL in frontend config
- CORS not configured

## Performance Testing

### Upload Large File
```bash
# Create test PDF ~40MB
# Upload and monitor:
- Network tab for request size
- Console for errors
- Progress indicator accuracy
```

### Many Documents
```bash
# Upload 50+ documents
# Verify:
- Pagination works smoothly
- Search is responsive
- Sorting is fast
- Grid renders without lag
```

## Success Criteria

✅ All test cases pass  
✅ No console errors  
✅ No network failures  
✅ UI is responsive  
✅ Error messages are clear  
✅ User experience is smooth  
✅ Data persists correctly  

## Next Steps After Testing

1. **Fix any issues** found during testing
2. **Add unit tests** for critical components
3. **Add integration tests** for workflows
4. **Performance optimization** if needed
5. **Security audit** before production
6. **User acceptance testing** with real users

## Production Checklist

Before deploying to production:
- [ ] Environment variables secured
- [ ] HTTPS enabled
- [ ] S3 bucket has proper permissions
- [ ] Database has backups
- [ ] Error tracking configured (Sentry)
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] CORS restricted to production domains
- [ ] Secrets rotated
- [ ] Documentation complete

## Support

**Backend API Documentation**: http://localhost:8000/docs  
**Frontend Documentation**: See `DOCUMENT_UI.md`  
**Backend Tests**: Run `pytest` in backend/  
**Frontend Logs**: Check browser console (F12)
