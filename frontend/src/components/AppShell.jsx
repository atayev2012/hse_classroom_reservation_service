import {
  CalendarDays,
  CalendarRange,
  DoorOpen,
  LayoutDashboard,
  LogOut,
  SlidersHorizontal,
  UsersRound
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';

import ConfirmModal from './ConfirmModal.jsx';
import Logo from './Logo.jsx';
import { authApi } from '../utils/api.js';
import { clearSession } from '../utils/storage.js';
import { canAccessPath, getCurrentRole } from '../utils/access.js';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Расписание', path: '/schedule', icon: CalendarDays },
  { label: 'Бронирование', path: '/booking', icon: DoorOpen },
  { label: 'Настр. расписаний', path: '/schedule-settings', icon: CalendarRange },
  { label: 'Настр. бронирований', path: '/booking-settings', icon: SlidersHorizontal },
  { label: 'Настр. пользователей', path: '/user-settings', icon: UsersRound }
];

const titles = {
  '/dashboard': ['Dashboard', 'Dashboard'],
  '/schedule': ['Schedule', 'Расписание'],
  '/booking': ['Booking', 'Бронирование'],
  '/schedule-settings': ['Schedule Settings', 'Настройки расписаний'],
  '/booking-settings': ['Booking Settings', 'Настройки бронирований'],
  '/user-settings': ['User Settings', 'Настройки пользователей']
};

export default function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [confirmLogout, setConfirmLogout] = useState(false);
  const role = getCurrentRole();
  const visibleNavItems = navItems.filter((item) => canAccessPath(item.path, role));
  const [crumb, title] = titles[location.pathname] || ['Page', 'Dashboard'];

  async function logout() {
    await authApi.logout().catch(() => {});
    clearSession();
    navigate('/login');
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink className="sidebar-logo" to="/dashboard" aria-label="Dashboard">
          <Logo />
        </NavLink>
        <nav className="sidebar-nav">
          {visibleNavItems.map(({ label, path, icon: Icon }) => (
            <NavLink key={path} to={path} className="nav-item">
              <Icon size={21} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <button className="logout-button" type="button" onClick={() => setConfirmLogout(true)}>
          <LogOut size={20} />
          <span>Выйти</span>
        </button>
      </aside>
      <main className="page-area">
        <div className="page-heading">
          <div className="breadcrumb">Page / {crumb}</div>
          <h1>{title}</h1>
        </div>
        <Outlet />
      </main>
      {confirmLogout && (
        <ConfirmModal
          title="Выход из системы"
          message="Вы уверены, что хотите выйти?"
          confirmLabel="Да"
          cancelLabel="Нет"
          onCancel={() => setConfirmLogout(false)}
          onConfirm={logout}
        />
      )}
    </div>
  );
}
