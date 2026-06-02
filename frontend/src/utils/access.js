import { getAccessToken, getStoredUser } from './storage.js';

export const roles = {
  STUDENT: 'student',
  EMPLOYEE: 'employee',
  MANAGER: 'manager',
  ADMIN: 'admin'
};

export const routeAccess = {
  '/dashboard': [roles.STUDENT, roles.EMPLOYEE, roles.MANAGER, roles.ADMIN],
  '/schedule': [roles.STUDENT, roles.EMPLOYEE, roles.MANAGER, roles.ADMIN],
  '/booking': [roles.EMPLOYEE, roles.MANAGER, roles.ADMIN],
  '/schedule-settings': [roles.MANAGER, roles.ADMIN],
  '/booking-settings': [roles.MANAGER, roles.ADMIN],
  '/user-settings': [roles.ADMIN]
};

export function normalizeRole(value) {
  const role = String(value || '').toLowerCase();
  return Object.values(roles).includes(role) ? role : null;
}

export function decodeTokenPayload(token = getAccessToken()) {
  if (!token) return null;

  try {
    const [, payload] = token.split('.');
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      '='
    );
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

export function getCurrentRole() {
  const tokenPayload = decodeTokenPayload();
  const storedUser = getStoredUser();
  return (
    normalizeRole(storedUser?.role) ||
    normalizeRole(storedUser?.type) ||
    normalizeRole(tokenPayload?.role) ||
    normalizeRole(tokenPayload?.user_type) ||
    normalizeRole(tokenPayload?.type) ||
    roles.STUDENT
  );
}

export function canAccessPath(path, role = getCurrentRole()) {
  const allowedRoles = routeAccess[path];
  return !allowedRoles || allowedRoles.includes(role);
}
