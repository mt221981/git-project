import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import VerdictsList from './pages/VerdictsList';
import VerdictDetail from './pages/VerdictDetail';
import ArticlesList from './pages/ArticlesListEnhanced';
import ArticleDetail from './pages/ArticleDetail';
import UploadVerdict from './pages/UploadVerdict';
import WordPressManagement from './pages/WordPressManagement';
import PublishingDashboard from './pages/PublishingDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark text-[#111618] dark:text-white">
      {/* Header / TopNavBar */}
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-[#dbe2e6] dark:border-[#2d3a41] bg-white dark:bg-background-dark px-10 py-3">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4 text-primary">
            <div className="size-8 flex items-center justify-center bg-primary/10 rounded-lg">
              <span className="material-symbols-outlined text-primary">gavel</span>
            </div>
            <h2 className="text-[#111618] dark:text-white text-lg font-bold leading-tight tracking-[-0.015em]">
              CMS משפטי
            </h2>
          </div>
          <label className="flex flex-col min-w-40 !h-10 max-w-64">
            <div className="flex w-full flex-1 items-stretch rounded-xl h-full">
              <div
                className="text-[#607c8a] flex border-none bg-[#f0f3f5] dark:bg-[#1c2a31] items-center justify-center pr-4 rounded-r-xl"
              >
                <span className="material-symbols-outlined">search</span>
              </div>
              <input
                className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-[#111618] dark:text-white focus:outline-0 focus:ring-0 border-none bg-[#f0f3f5] dark:bg-[#1c2a31] focus:border-none h-full placeholder:text-[#607c8a] px-4 rounded-r-none pl-2 text-base font-normal leading-normal"
                placeholder="חיפוש..."
              />
            </div>
          </label>
        </div>
        <div className="flex flex-1 justify-end gap-8">
          <div className="flex items-center gap-9">
            <Link
              to="/"
              className={`text-sm font-medium leading-normal hover:text-primary transition-colors ${
                isActive('/') && location.pathname === '/' ? 'text-primary' : 'text-[#111618] dark:text-white'
              }`}
            >
              דף הבית
            </Link>
            <Link
              to="/verdicts"
              className={`text-sm font-medium leading-normal hover:text-primary transition-colors ${
                isActive('/verdicts') ? 'text-primary' : 'text-[#111618] dark:text-white'
              }`}
            >
              פסקי דין
            </Link>
            <Link
              to="/articles"
              className={`text-sm font-medium leading-normal hover:text-primary transition-colors ${
                isActive('/articles') ? 'text-primary' : 'text-[#111618] dark:text-white'
              }`}
            >
              מאמרים
            </Link>
            <Link
              to="/publishing"
              className={`text-sm font-medium leading-normal hover:text-primary transition-colors ${
                isActive('/publishing') ? 'text-primary' : 'text-[#111618] dark:text-white'
              }`}
            >
              לוח פרסום
            </Link>
            <Link
              to="/wordpress"
              className={`text-sm font-medium leading-normal hover:text-primary transition-colors ${
                isActive('/wordpress') ? 'text-primary' : 'text-[#111618] dark:text-white'
              }`}
            >
              WordPress
            </Link>
            <Link
              to="/upload"
              className={`text-sm font-medium leading-normal hover:text-primary transition-colors ${
                isActive('/upload') ? 'text-primary' : 'text-[#111618] dark:text-white'
              }`}
            >
              העלאה חדשה
            </Link>
          </div>
          <div className="flex gap-2">
            <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 bg-[#f0f3f5] dark:bg-[#1c2a31] text-[#111618] dark:text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-2.5">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 bg-[#f0f3f5] dark:bg-[#1c2a31] text-[#111618] dark:text-white gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-2.5">
              <span className="material-symbols-outlined">language</span>
            </button>
          </div>
          <div
            className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-primary/20"
            style={{
              backgroundImage:
                'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBAMCwZCg3YBpnIzsCaZYM4kvNmiIzPtNb40ThHNCl59qh62Is0BIAnycb422A6OE_klv5P8Dk9D2U0zzm0inqTOlR--0KM5uJJAVoLlAr-7A5EvsJvNQRNEbkA8NaPiB_ywJyEcRNnNAdLFOVxBbo4jwUWKSw_7uVg5Z8jyE_29EQWDiuQ43R2rVkybZB2kd8T8y3ge0JQT0IYfTiP1920BZaqFYZrGG_hakQXBPA6Qn7pe4mKVAzqiZbyp-bH00Be8oEWELTmxMFH")',
            }}
            title="פרופיל משתמש"
          ></div>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/verdicts" element={<VerdictsList />} />
        <Route path="/verdicts/:id" element={<VerdictDetail />} />
        <Route path="/articles" element={<ArticlesList />} />
        <Route path="/articles/:id" element={<ArticleDetail />} />
        <Route path="/publishing" element={<PublishingDashboard />} />
        <Route path="/wordpress" element={<WordPressManagement />} />
        <Route path="/upload" element={<UploadVerdict />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
