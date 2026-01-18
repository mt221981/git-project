# Legal Content System - Frontend

Modern React-based web interface for the Legal Content System.

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Axios** - HTTP client
- **React Dropzone** - Drag-and-drop file upload

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Backend URL

The frontend is configured to proxy `/api` requests to `http://localhost:8000` (the backend server).

If your backend is running on a different port, update `vite.config.ts`:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:YOUR_PORT',
    changeOrigin: true,
  },
},
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at **http://localhost:3000**

### 4. Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### 5. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client with all backend endpoints
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main dashboard with statistics
│   │   ├── UploadVerdict.tsx  # File upload with drag-and-drop
│   │   ├── VerdictsList.tsx   # List all verdicts
│   │   ├── VerdictDetail.tsx  # Verdict details and actions
│   │   ├── ArticlesList.tsx   # List all articles
│   │   └── ArticleDetail.tsx  # Article details and publishing
│   ├── App.tsx                # Main app with routing
│   ├── main.tsx               # Application entry point
│   └── index.css              # Global styles and Tailwind
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Features

### Dashboard
- **Statistics Overview**: Total verdicts, anonymized count, articles count, published count
- **Status Distribution**: Verdicts by status
- **Quality Scores**: Average scores for content, SEO, readability, and E-E-A-T
- **Quick Actions**: Upload new verdict, view all verdicts

### Upload Verdict
- **Drag-and-Drop**: Drop files or click to select
- **File Validation**: Only PDF, TXT, DOC, DOCX files allowed
- **Size Limit**: 50MB maximum
- **Progress Indication**: Visual feedback during upload
- **Auto-Redirect**: Automatically redirects to verdict detail after upload

### Verdicts List
- **All Verdicts**: Browse all uploaded verdicts
- **Status Badges**: Visual indication of processing status
- **Quick View**: Case number, court name, status
- **Navigation**: Click to view details

### Verdict Detail
- **Full Information**: Case number, court, judge, legal area, status
- **Action Buttons**:
  - **Anonymize** (if status is 'extracted')
  - **Analyze** (if status is 'anonymized')
  - **Generate Article** (if status is 'analyzed')
- **Progress Workflow**: Step-by-step processing

### Articles List
- **All Articles**: Browse generated articles
- **Preview**: Title, excerpt, word count
- **Quality Scores**: Overall score badge
- **Publish Status**: Draft/Ready/Published indication

### Article Detail
- **Full Content**: Complete article HTML
- **Metadata**: Word count, reading time, scores
- **Quality Breakdown**: Individual scores for content, SEO, readability, E-E-A-T
- **WordPress Publishing**: Publish to configured WordPress sites

## Complete Workflow

### 1. Upload a Verdict

1. Click "העלאה חדשה" (New Upload) in navigation
2. Drag and drop a PDF/DOC/TXT file or click to select
3. Wait for upload to complete
4. You'll be redirected to the verdict detail page

### 2. Process the Verdict

On the verdict detail page:

1. Click **"אנוניזם"** (Anonymize) to anonymize personal information
   - Wait for the process to complete
   - Page will refresh automatically

2. Click **"נתח"** (Analyze) to extract structured information
   - The system extracts facts, legal questions, principles, etc.
   - Page will refresh when done

3. Click **"צור מאמר"** (Create Article) to generate SEO article
   - This generates a complete SEO-optimized article
   - You'll be redirected to the article page

### 3. Review and Publish Article

On the article detail page:

1. Review the generated content
2. Check quality scores
3. Click **"פרסם ל-WordPress"** (Publish to WordPress)
4. Select the WordPress site
5. Article is published!

## API Integration

The frontend communicates with the backend via the API client (`src/api/client.ts`).

### Available API Methods

#### Verdicts
- `verdictApi.upload(file)` - Upload verdict file
- `verdictApi.list(params)` - List verdicts
- `verdictApi.get(id)` - Get verdict details
- `verdictApi.anonymize(id)` - Anonymize verdict
- `verdictApi.delete(id)` - Delete verdict
- `verdictApi.getStats()` - Get statistics

#### Articles
- `articleApi.analyze(verdictId)` - Analyze verdict
- `articleApi.generate(verdictId)` - Generate article
- `articleApi.list(params)` - List articles
- `articleApi.get(id)` - Get article details
- `articleApi.getByVerdict(verdictId)` - Get article by verdict
- `articleApi.getStats()` - Get statistics

#### WordPress
- `wordpressApi.listSites()` - List WordPress sites
- `wordpressApi.createSite(data)` - Add WordPress site
- `wordpressApi.publish(articleId, data)` - Publish article

## Customization

### Colors

Edit `tailwind.config.js` to customize the color scheme:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      },
    },
  },
},
```

### RTL Support

The application is configured for Hebrew (RTL) by default.

To change to LTR:
1. Update `index.html`: `<html lang="en" dir="ltr">`
2. Update `src/index.css`: Remove or modify RTL rules

### Adding New Pages

1. Create a new component in `src/pages/`
2. Add route in `src/App.tsx`:

```typescript
<Route path="/your-path" element={<YourComponent />} />
```

3. Add navigation link:

```typescript
<Link to="/your-path">Your Page</Link>
```

## Troubleshooting

### Backend Connection Issues

**Error**: "Network Error" or "Failed to fetch"

**Solution**:
1. Ensure backend is running: `cd backend && python app/main.py`
2. Check backend is on port 8000
3. Verify proxy configuration in `vite.config.ts`

### Build Errors

**Error**: "Module not found" or TypeScript errors

**Solution**:
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Styling Issues

**Error**: Tailwind styles not applying

**Solution**:
1. Ensure `index.css` is imported in `main.tsx`
2. Check Tailwind config includes all source files
3. Restart dev server

## Development Tips

### Hot Module Replacement (HMR)

Vite provides instant updates during development. Changes to React components will update in the browser without full page reload.

### React Query DevTools

Add React Query DevTools for debugging:

```bash
npm install @tanstack/react-query-devtools
```

Then in `App.tsx`:
```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Inside QueryClientProvider
<ReactQueryDevtools initialIsOpen={false} />
```

### TypeScript Strict Mode

The project uses TypeScript strict mode. This catches potential bugs early but may require more explicit typing.

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Performance

The application is optimized for performance:
- Code splitting with React lazy loading
- React Query caching reduces API calls
- Tailwind CSS purging removes unused styles
- Vite optimizes build output

## License

Proprietary
