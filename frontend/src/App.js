import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import Sidebar from "./components/Sidebar";
import NotificationCenter from "./components/NotificationCenter";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import SearchPage from "./pages/SearchPage";
import PipelinePage from "./pages/PipelinePage";
import CompanyDetailPage from "./pages/CompanyDetailPage";
import RemindersPage from "./pages/RemindersPage";
import { Toaster } from "./components/ui/sonner";
import { useState } from "react";
import { List } from "@phosphor-icons/react";
import "./App.css";

function ProtectedLayout() {
  const { user, loading } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F9F9FB]">
        <div className="w-8 h-8 border-2 border-[#002FA7] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen flex bg-[#F9F9FB]">
      <div className="hidden lg:block flex-shrink-0">
        <div className="sticky top-0 h-screen"><Sidebar /></div>
      </div>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/20" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full"><Sidebar onClose={() => setMobileOpen(false)} /></div>
        </div>
      )}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-40 bg-white border-b border-[#E4E4E7] h-12 flex items-center px-4 gap-3">
          <button data-testid="mobile-menu-button" onClick={() => setMobileOpen(true)} className="lg:hidden p-1.5 hover:bg-[#F4F4F5] rounded-sm">
            <List size={20} className="text-[#0A0A0A]" />
          </button>
          <div className="flex-1" />
          <NotificationCenter />
          <span className="text-sm font-body text-[#0A0A0A] hidden sm:block">{user.name || user.email || user.phone}</span>
        </header>
        <main className="flex-1 overflow-auto"><Outlet /></main>
      </div>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/pipeline" element={<PipelinePage />} />
              <Route path="/company/:id" element={<CompanyDetailPage />} />
              <Route path="/reminders" element={<RemindersPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
