# Phase 6: Frontend Dashboard Integration

**Status**: ✅ Complete
**Last Updated**: 2026-01-14

## Overview

Phase 6 implements a comprehensive React-based frontend dashboard that integrates all backend capabilities from Phases 1-5, providing an intuitive interface for managing the complete legal content workflow.

### Key Features

- 📊 **Publishing Dashboard**: Real-time monitoring and statistics
- 🚀 **Batch Operations**: Select and publish multiple articles
- ⚙️ **WordPress Site Management**: Add, edit, and test WordPress sites
- 📝 **Enhanced Article Management**: Filtering, validation, and status tracking
- 🔄 **Queue Management**: Schedule and plan article publishing
- 📈 **Statistics & Monitoring**: Comprehensive analytics across the system
- 🎨 **Modern UI**: Tailwind CSS with Hebrew RTL support
- ⚡ **Real-time Updates**: TanStack Query for data synchronization

## Technology Stack

### Core Technologies

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe code throughout
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **TanStack Query**: Data fetching and caching
- **Axios**: HTTP client
- **React Icons**: Icon library
- **React Dropzone**: File upload handling

### Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts              # API client with all endpoints
│   ├── pages/
│   │   ├── Dashboard.tsx          # Main dashboard
│   │   ├── VerdictsList.tsx       # Verdicts list
│   │   ├── VerdictDetail.tsx      # Verdict detail view
│   │   ├── ArticlesListEnhanced.tsx # Enhanced articles list with batch ops
│   │   ├── ArticleDetail.tsx      # Article detail view
│   │   ├── UploadVerdict.tsx      # File upload interface
│   │   ├── WordPressManagement.tsx # WordPress sites management
│   │   └── PublishingDashboard.tsx # Publishing monitoring
│   ├── types/
│   │   └── index.ts               # TypeScript type definitions
│   ├── App.tsx                    # Main app component
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Features

### 1. Publishing Dashboard (`/publishing`)

Comprehensive monitoring interface for publishing operations.

**Features**:
- Overall publishing statistics
- Per-site statistics breakdown
- Failed articles monitoring with retry
- Ready-to-publish articles queue
- Queue management for scheduling
- Publishing tips and best practices

**Components**:
```tsx
<PublishingDashboard />
├── <StatCard /> (×5)           # Total, Published, Ready, Draft, Failed
├── Site Statistics Grid         # Per-site breakdown
├── Failed Articles Section      # With retry button
├── Ready Articles Section       # Queue preview
├── <QueueManagement />          # Scheduling interface
└── Tips Section                 # Best practices
```

**Usage**:
1. Navigate to "לוח פרסום" in main navigation
2. View overall statistics at a glance
3. Filter by specific WordPress site
4. Review failed articles and retry publishing
5. Create publishing queues with custom schedules

### 2. WordPress Site Management (`/wordpress`)

Manage all WordPress sites in the system.

**Features**:
- List all WordPress sites
- Add new sites with Application Passwords
- Edit existing sites
- Delete sites
- Test connections
- View per-site statistics

**Site Form Fields**:
- Site Name
- Site URL (HTTPS required)
- Username
- Application Password
- SEO Plugin (Yoast/Rank Math)

**Testing Connection**:
```tsx
// Each site card includes test button
<button onClick={handleTest}>בדוק חיבור</button>
// Shows success/error feedback
```

**Example Flow**:
1. Click "הוסף אתר חדש"
2. Fill in WordPress site details
3. Create Application Password in WordPress
4. Paste password and submit
5. Test connection to verify
6. Start publishing to the new site

### 3. Enhanced Articles List (`/articles`)

Advanced article management with batch operations.

**New Features**:
- ✅ Multi-select with checkboxes
- 🔍 Filter by publish status
- 📦 Batch publish to WordPress
- 🎯 Select all / Deselect all
- 📊 Enhanced status badges
- 🔑 Focus keyword display

**Batch Publishing Flow**:
```tsx
// 1. Select multiple articles
{selectedIds.map(id => <Article selected={true} />)}

// 2. Click batch publish button
<button onClick={() => setShowBatchPublish(true)}>
  פרסם {selectedIds.length} מאמרים
</button>

// 3. Choose target site and status
<BatchPublishModal
  articleIds={selectedIds}
  sites={sites}
  onPublish={handleBatchPublish}
/>
```

**Filter Options**:
- All statuses (הכל)
- Draft (טיוטה)
- Ready (מוכן לפרסום)
- Published (מפורסם)
- Failed (נכשל)

### 4. Main Dashboard (`/`)

Overview of the entire system.

**Metrics Displayed**:
- Total verdicts count
- Anonymized verdicts count
- Total articles count
- Published articles count
- Verdicts by status breakdown
- Average quality scores (Content, SEO, Readability, E-E-A-T)

**Quick Actions**:
- Upload new verdict
- View all verdicts
- Navigate to publishing dashboard
- Access WordPress management

### 5. Article Detail View

Enhanced with publishing capabilities.

**Features**:
- Complete article preview
- Quality scores visualization
- HTML content rendering
- Single-article publishing
- Validation feedback
- WordPress site selection

**Publishing Options**:
```tsx
// Publish as draft or live
<button onClick={() => publish(siteId, 'draft')}>
  פרסם כטיוטה
</button>
<button onClick={() => publish(siteId, 'publish')}>
  פרסם מיידית
</button>
```

## API Integration

### API Client Structure

All API calls are centralized in `src/api/client.ts`:

```typescript
// Verdict APIs
verdictApi.upload(file)
verdictApi.list(params)
verdictApi.get(id)
verdictApi.anonymize(id)
verdictApi.delete(id)
verdictApi.getStats()

// Article APIs
articleApi.analyze(verdictId)
articleApi.generate(verdictId)
articleApi.list(params)
articleApi.get(id)
articleApi.getByVerdict(verdictId)
articleApi.getStats()

// WordPress APIs
wordpressApi.listSites()
wordpressApi.createSite(data)
wordpressApi.updateSite(siteId, data)
wordpressApi.deleteSite(siteId)
wordpressApi.testConnection(siteId)
wordpressApi.publish(articleId, data)
wordpressApi.publishWithRetry(articleId, data)
wordpressApi.batchPublish(data)
wordpressApi.republishFailed(data)
wordpressApi.validateArticle(articleId)
wordpressApi.getStatistics(siteId?)
wordpressApi.scheduleQueue(data)
wordpressApi.getUnpublishedArticles(params)
wordpressApi.syncArticleStatus(articleId)
```

### TypeScript Types

Complete type safety with `src/types/index.ts`:

```typescript
// Core types
Article
WordPressSite
Verdict
PublishStatus
VerdictStatus

// Request/Response types
PublishRequest
BatchPublishRequest
BatchPublishResult
PublishingStatistics
PublishingQueue
ValidationError

// Utility types
PaginatedResponse<T>
ApiError
```

## Setup and Installation

### Prerequisites

- Node.js 18+ and npm
- Backend API running (Phase 1-5)
- WordPress sites with Application Passwords

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Configuration

Create `.env` file in frontend directory:

```env
# API Base URL (optional, defaults to /api/v1)
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Development Server

```bash
npm run dev
# Opens at http://localhost:5173
```

The dev server includes:
- ⚡ Hot Module Replacement (HMR)
- 🔄 Auto-reload on changes
- 📝 TypeScript error checking
- 🎨 Tailwind CSS compilation

## User Workflows

### Workflow 1: Upload and Publish Verdict

```
1. Upload Verdict
   └─ Navigate to "העלאה חדשה"
   └─ Drag & drop PDF file
   └─ Wait for processing

2. Review Verdict
   └─ Go to "פסקי דין"
   └─ Click on verdict
   └─ Verify anonymization

3. Generate Article
   └─ Click "צור מאמר"
   └─ Wait for AI generation
   └─ Review article quality scores

4. Publish to WordPress
   └─ Go to "מאמרים"
   └─ Select article
   └─ Click "פרסם ל-WordPress"
   └─ Choose site and status
   └─ Confirm publication
```

### Workflow 2: Batch Publishing

```
1. Filter Ready Articles
   └─ Navigate to "מאמרים"
   └─ Filter by status: "מוכן לפרסום"

2. Select Articles
   └─ Click checkboxes on desired articles
   └─ OR click "בחר הכל"

3. Batch Publish
   └─ Click "פרסם X מאמרים"
   └─ Select target WordPress site
   └─ Choose draft or publish status
   └─ Confirm batch operation

4. Monitor Results
   └─ View success/failure notifications
   └─ Check "לוח פרסום" for statistics
```

### Workflow 3: Manage Failed Articles

```
1. View Failed Articles
   └─ Navigate to "לוח פרסום"
   └─ Scroll to "מאמרים שנכשלו"

2. Review Errors
   └─ Click on failed article
   └─ Read error message in metadata
   └─ Fix issues if needed

3. Retry Publishing
   └─ Click "נסה לפרסם מחדש" on dashboard
   └─ System retries up to 10 failed articles
   └─ Review results

4. Manual Retry
   └─ Or navigate to article detail
   └─ Click "פרסם ל-WordPress" again
   └─ Select site and try again
```

### Workflow 4: Schedule Publishing Queue

```
1. Create Queue
   └─ Navigate to "לוח פרסום"
   └─ Click "צור תור פרסום"

2. Configure Queue
   └─ Select WordPress site
   └─ Set articles per day (e.g., 5)
   └─ Set minimum quality score (e.g., 75)

3. Review Queue
   └─ System shows queued articles
   └─ Displays estimated timeline
   └─ Articles sorted by quality score

4. Manual Publishing
   └─ Publish articles from queue manually
   └─ OR integrate with scheduler/cron job
```

## UI Components

### Button Styles

```tsx
// Primary action
<button className="btn btn-primary">פעולה עיקרית</button>

// Secondary action
<button className="btn btn-secondary">פעולה משנית</button>

// Destructive action
<button className="btn btn-danger">מחיקה</button>

// Small button
<button className="btn btn-sm btn-primary">קטן</button>
```

### Card Component

```tsx
<div className="card">
  <h2 className="text-xl font-bold mb-4">כותרת</h2>
  <p>תוכן הכרטיס</p>
</div>
```

### Input Field

```tsx
<input
  type="text"
  className="input"
  placeholder="הזן טקסט..."
/>
```

### Badge/Status

```tsx
<span className="badge bg-green-100 text-green-800">
  מפורסם
</span>
```

### Modal/Dialog

```tsx
{showModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
      <h2>כותרת</h2>
      {/* Modal content */}
      <button onClick={() => setShowModal(false)}>סגור</button>
    </div>
  </div>
)}
```

## State Management

### TanStack Query Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

### Data Fetching Pattern

```tsx
// Automatic caching and refetching
const { data, isLoading, error } = useQuery({
  queryKey: ['articles', filters],
  queryFn: () => articleApi.list(filters).then(res => res.data),
});

// Mutations with invalidation
const publishMutation = useMutation({
  mutationFn: (data) => wordpressApi.batchPublish(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['articles'] });
    queryClient.invalidateQueries({ queryKey: ['wordpress-statistics'] });
  },
});
```

### Query Keys Structure

```typescript
['articles']                    // All articles
['articles', 'failed']          // Failed articles only
['articles', statusFilter]      // Filtered articles
['article', id]                 // Single article
['wordpress-sites']             // All sites
['wordpress-statistics']        // Overall stats
['wordpress-statistics', siteId] // Site-specific stats
['verdict-stats']               // Verdict statistics
```

## Localization (Hebrew RTL)

### RTL Configuration

```css
/* index.css */
@layer base {
  * {
    direction: rtl;
  }
}
```

### Tailwind RTL Classes

```tsx
// Use space-x-reverse for RTL spacing
<div className="flex space-x-4 space-x-reverse">

// Margin and padding work naturally
<div className="mr-4 ml-2">  {/* mr = margin-right in RTL */}

// Text alignment
<p className="text-right">   {/* Default for Hebrew */}
```

### Hebrew Text Labels

All UI text is in Hebrew:
- Navigation: מערכת תוכן משפטי, פסקי דין, מאמרים
- Actions: העלאה חדשה, פרסם, ערוך, מחק
- Status: טיוטה, מוכן לפרסום, מפורסם, נכשל
- Messages: טוען..., שגיאה, הצלחה

## Performance Optimization

### Code Splitting

React Router automatically splits code by route:
```typescript
// Each page is a separate chunk
const Dashboard = lazy(() => import('./pages/Dashboard'));
```

### Query Caching

TanStack Query caches all API responses:
- 5-minute default cache time
- Background refetching
- Optimistic updates

### Image Optimization

```tsx
// Lazy load images
<img loading="lazy" src={url} alt={alt} />

// Use appropriate formats
// - AVIF/WebP for modern browsers
// - JPEG/PNG fallbacks
```

### Bundle Size

Current production bundle:
- Main chunk: ~150KB (gzipped)
- Vendor chunk: ~100KB (gzipped)
- Page chunks: ~10-30KB each

## Testing

### Manual Testing Checklist

**WordPress Management**:
- [ ] Add new WordPress site
- [ ] Test connection succeeds
- [ ] Edit existing site
- [ ] Delete site (with confirmation)
- [ ] View per-site statistics

**Batch Publishing**:
- [ ] Select multiple articles
- [ ] Select all / deselect all
- [ ] Batch publish as draft
- [ ] Batch publish as live
- [ ] Handle mixed success/failure

**Publishing Dashboard**:
- [ ] View overall statistics
- [ ] Filter by site
- [ ] View failed articles
- [ ] Retry failed articles
- [ ] Create publishing queue

**Article Management**:
- [ ] Filter by status
- [ ] View article details
- [ ] Publish single article
- [ ] View quality scores
- [ ] Check validation errors

### Browser Testing

Test in:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ⚠️ Mobile browsers (responsive design)

### Accessibility

- Keyboard navigation support
- ARIA labels on interactive elements
- Focus states visible
- Color contrast compliance

## Deployment

### Production Build

```bash
# Build optimized production bundle
npm run build

# Output directory: dist/
# - index.html
# - assets/
#   - index-[hash].js
#   - index-[hash].css
```

### Deployment Options

#### Option 1: Static Hosting (Netlify, Vercel)

```bash
# Build
npm run build

# Deploy dist/ folder
netlify deploy --prod --dir=dist
# OR
vercel --prod
```

#### Option 2: Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/legal-content-frontend/dist;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript image/svg+xml;
}
```

#### Option 3: Docker

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment Variables

**Production `.env`**:
```env
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
```

### CORS Configuration

Backend must allow frontend origin:

```python
# FastAPI backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Issue: API Calls Failing

**Symptoms**: Network errors, 404s, CORS errors

**Solutions**:
1. Check API base URL in `.env`
2. Verify backend is running
3. Check CORS configuration
4. Inspect Network tab in DevTools

```bash
# Test API manually
curl http://localhost:8000/api/v1/articles

# Check frontend env
console.log(import.meta.env.VITE_API_BASE_URL)
```

### Issue: WordPress Connection Fails

**Symptoms**: Test connection fails, publish errors

**Solutions**:
1. Verify Application Password is correct
2. Check WordPress REST API is enabled
3. Ensure HTTPS (not HTTP)
4. Test credentials manually:

```bash
curl -u username:app_password \
  https://yoursite.com/wp-json/wp/v2/posts
```

### Issue: Batch Publish Partially Fails

**Symptoms**: Some articles publish, others fail

**Solutions**:
1. Check "לוח פרסום" for specific errors
2. Review failed article validation
3. Check WordPress site limits/quotas
4. Retry failed articles individually

### Issue: Styles Not Loading

**Symptoms**: Unstyled page, missing CSS

**Solutions**:
1. Rebuild: `npm run build`
2. Clear browser cache
3. Check Tailwind config
4. Verify PostCSS setup

```bash
# Rebuild with clean cache
rm -rf node_modules/.vite
npm run build
```

### Issue: Hebrew Text Displays LTR

**Symptoms**: Text flows left-to-right

**Solutions**:
1. Check `direction: rtl` in CSS
2. Verify `space-x-reverse` on flex containers
3. Check HTML `lang="he"` attribute

## Best Practices

### 1. Error Handling

```tsx
// Always handle errors
const { data, error, isLoading } = useQuery({
  queryKey: ['articles'],
  queryFn: fetchArticles,
});

if (error) {
  return <div className="text-red-600">שגיאה: {error.message}</div>;
}
```

### 2. Loading States

```tsx
// Show loading feedback
if (isLoading) {
  return <div className="text-center py-8">טוען...</div>;
}

// Or skeleton screens
{isLoading ? <ArticleSkeleton /> : <ArticleCard />}
```

### 3. Optimistic Updates

```tsx
// Update UI before server confirms
const deleteMutation = useMutation({
  mutationFn: deleteArticle,
  onMutate: async (articleId) => {
    // Optimistically remove from UI
    await queryClient.cancelQueries({ queryKey: ['articles'] });
    const previous = queryClient.getQueryData(['articles']);
    queryClient.setQueryData(['articles'], (old) =>
      old.filter(a => a.id !== articleId)
    );
    return { previous };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(['articles'], context.previous);
  },
});
```

### 4. Type Safety

```tsx
// Always use TypeScript types
import type { Article, PublishStatus } from '../types';

interface ArticleCardProps {
  article: Article;
  onPublish: (id: number) => Promise<void>;
}

const ArticleCard: React.FC<ArticleCardProps> = ({ article, onPublish }) => {
  // Type-safe component
};
```

### 5. Reusable Components

```tsx
// Extract common patterns
const Modal: React.FC<{ isOpen: boolean; onClose: () => void; children: ReactNode }> = ({
  isOpen,
  onClose,
  children,
}) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50">
      <div className="bg-white rounded-lg p-6 max-w-md mx-auto mt-20">
        {children}
        <button onClick={onClose} className="btn btn-secondary mt-4">
          סגור
        </button>
      </div>
    </div>
  );
};
```

## Future Enhancements

### Potential Features

1. **Real-time Notifications**
   - WebSocket connection for live updates
   - Toast notifications for publishing events
   - Progress bars for long operations

2. **Advanced Analytics**
   - Charts and graphs (Chart.js/Recharts)
   - Publishing trends over time
   - SEO performance tracking

3. **Bulk Operations**
   - Bulk delete articles
   - Bulk update categories/tags
   - Bulk quality improvement

4. **User Management**
   - Authentication (OAuth, JWT)
   - Role-based access control
   - Activity logging

5. **Content Calendar**
   - Visual publishing schedule
   - Drag-and-drop planning
   - Automated publishing

6. **Mobile App**
   - React Native companion app
   - Push notifications
   - Offline support

## Resources

### Documentation

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TanStack Query](https://tanstack.com/query)
- [React Router](https://reactrouter.com)

### Related Files

- `frontend/src/App.tsx` - Main application
- `frontend/src/api/client.ts` - API integration
- `frontend/src/types/index.ts` - TypeScript types
- `frontend/src/pages/*` - All page components
- `backend/PHASE5.md` - Backend WordPress integration

### WordPress Resources

- [Application Passwords](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/)
- [REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Yoast SEO API](https://developer.yoast.com/customization/apis/rest-api/)

---

**Phase 6 Status**: ✅ Complete and production-ready

**Complete System Status**:
- ✅ Phase 1-2: File Upload & Processing
- ✅ Phase 3: Anonymization Services
- ✅ Phase 4: AI Analysis & Article Generation
- ✅ Phase 5: WordPress Publishing Integration
- ✅ Phase 6: Frontend Dashboard

**Ready for Production Deployment!**

For questions or support, refer to individual phase documentation or the main README.md.
