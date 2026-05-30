import { Navigate, Route, Routes } from 'react-router-dom';
import { useEffect, useState } from 'react';

import AppShell from './components/AppShell.jsx';
import { PageSkeleton } from './components/Skeleton.jsx';
import LoginPage from './pages/LoginPage.jsx';
import VerificationPage from './pages/VerificationPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import SchedulePage from './pages/SchedulePage.jsx';
import BookingPage from './pages/BookingPage.jsx';
import ScheduleSettingsPage from './pages/ScheduleSettingsPage.jsx';
import BookingSettingsPage from './pages/BookingSettingsPage.jsx';
import UserSettingsPage from './pages/UserSettingsPage.jsx';
import { hasActiveSession, setStoredUser } from './utils/storage.js';
import { canAccessPath, normalizeRole } from './utils/access.js';
import { authApi } from './utils/api.js';

function normalizeUser(user) {
  return {
    id: user?.id || user?.user_id,
    email: user?.email,
    type: normalizeRole(user?.role || user?.type) || 'student'
  };
}

function ProtectedRoute({ children, path }) {
  const [status, setStatus] = useState(() => (hasActiveSession() ? 'ready' : 'checking'));

  useEffect(() => {
    if (status !== 'checking') return undefined;

    let mounted = true;
    authApi.me()
      .then((user) => {
        if (!mounted) return;
        setStoredUser(normalizeUser(user));
        setStatus('ready');
      })
      .catch(() => {
        if (mounted) setStatus('guest');
      });

    return () => { mounted = false; };
  }, [status]);

  if (status === 'checking') return <div className="route-loading"><PageSkeleton widgets={2} /></div>;
  if (status === 'guest') return <Navigate to="/login" replace />;
  if (path && !canAccessPath(path)) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify" element={<VerificationPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<ProtectedRoute path="/dashboard"><DashboardPage /></ProtectedRoute>} />
        <Route path="schedule" element={<ProtectedRoute path="/schedule"><SchedulePage /></ProtectedRoute>} />
        <Route path="booking" element={<ProtectedRoute path="/booking"><BookingPage /></ProtectedRoute>} />
        <Route path="schedule-settings" element={<ProtectedRoute path="/schedule-settings"><ScheduleSettingsPage /></ProtectedRoute>} />
        <Route path="booking-settings" element={<ProtectedRoute path="/booking-settings"><BookingSettingsPage /></ProtectedRoute>} />
        <Route path="user-settings" element={<ProtectedRoute path="/user-settings"><UserSettingsPage /></ProtectedRoute>} />
      </Route>
    </Routes>
  );
}
