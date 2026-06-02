const ACCESS_TOKEN_KEY = 'hse_access_token';
const REFRESH_TOKEN_KEY = 'hse_refresh_token';
const USER_KEY = 'hse_user';
const PENDING_USER_ID_KEY = 'hse_pending_user_id';

function expireCookie(key) {
  document.cookie = `${key}=; Max-Age=0; path=/; SameSite=Lax`;
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function hasActiveSession() {
  return Boolean(getStoredUser()?.id || getAccessToken());
}

export function setTokens({ accessToken, refreshToken }) {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  if (!accessToken && !refreshToken) return;
}

export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(PENDING_USER_ID_KEY);
  expireCookie(ACCESS_TOKEN_KEY);
  expireCookie(REFRESH_TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function setStoredUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function setPendingUserId(userId) {
  localStorage.setItem(PENDING_USER_ID_KEY, String(userId));
}

export function getPendingUserId() {
  return localStorage.getItem(PENDING_USER_ID_KEY);
}
