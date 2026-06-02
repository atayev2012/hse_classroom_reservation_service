import { clearSession, getAccessToken, getRefreshToken, setTokens } from './storage.js';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

async function request(path, options = {}) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) headers.Authorization = `Bearer ${token}`;
  const refreshToken = getRefreshToken();
  if (refreshToken) headers['X-Refresh-Token'] = refreshToken;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers
  });

  let data = null;
  const text = await response.text();
  if (text) data = JSON.parse(text);

  if (!response.ok) {
    if (response.status === 401) clearSession();
    const detail = data?.detail || data?.status || 'Ошибка запроса';
    throw new Error(Array.isArray(detail) ? detail[0]?.msg : detail);
  }

  return data;
}

function toQuery(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== '') {
          search.append(key, item);
        }
      });
    } else if (value !== undefined && value !== null && value !== '') {
      search.set(key, value);
    }
  });
  const value = search.toString();
  return value ? `?${value}` : '';
}

export const authApi = {
  async login(email, deviceInfo = navigator.userAgent) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, device_info: deviceInfo })
    });
  },
  async verify(userId, verificationCode, deviceInfo = navigator.userAgent) {
    const response = await request('/auth/verify', {
      method: 'POST',
      body: JSON.stringify({
        user_id: Number(userId),
        verification_code: verificationCode,
        device_info: deviceInfo
      })
    });
    setTokens({
      accessToken: response.access_token,
      refreshToken: response.refresh_token
    });
    return response;
  },
  me: () => request('/auth/me'),
  logout: () => request('/auth/logout', { method: 'POST' }),
  students: (params) => request(`/auth/students${toQuery(params)}`),
  users: {
    list: (params) => request(`/auth/users${toQuery(params)}`),
    get: (id) => request(`/auth/users/${id}`),
    create: (payload) => request('/auth/users', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/auth/users/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/auth/users/${id}`, { method: 'DELETE' })
  }
};

export const bookingApi = {
  buildings: {
    list: (params) => request(`/booking/buildings${toQuery(params)}`),
    get: (id) => request(`/booking/buildings/${id}`),
    create: (payload) => request('/booking/buildings', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/booking/buildings/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/booking/buildings/${id}`, { method: 'DELETE' })
  },
  equipment: {
    list: (params) => request(`/booking/equipment${toQuery(params)}`),
    get: (id) => request(`/booking/equipment/${id}`),
    create: (payload) => request('/booking/equipment', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/booking/equipment/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/booking/equipment/${id}`, { method: 'DELETE' })
  },
  rooms: {
    list: (params) => request(`/booking/rooms${toQuery(params)}`),
    get: (id) => request(`/booking/rooms/${id}`),
    create: (payload) => request('/booking/rooms', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/booking/rooms/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/booking/rooms/${id}`, { method: 'DELETE' })
  },
  bookings: {
    list: (params) => request(`/booking/bookings${toQuery(params)}`),
    get: (id) => request(`/booking/bookings/${id}`),
    create: (payload) => request('/booking/bookings', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/booking/bookings/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/booking/bookings/${id}`, { method: 'DELETE' })
  }
};

export const scheduleApi = {
  schedules: {
    list: (params) => request(`/schedules${toQuery(params)}`),
    get: (id) => request(`/schedules/${id}`),
    create: (payload) => request('/schedules', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/${id}`, { method: 'DELETE' }),
    publish: (id) => request(`/schedules/${id}/publish`, { method: 'POST' }),
    unpublish: (id) => request(`/schedules/${id}/unpublish`, { method: 'POST' })
  },
  items: {
    list: (params) => request(`/schedules/items${toQuery(params)}`),
    create: (payload) => request('/schedules/items', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/items/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/items/${id}`, { method: 'DELETE' })
  },
  groups: {
    list: (params) => request(`/schedules/groups${toQuery(params)}`),
    create: (payload) => request('/schedules/groups', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/groups/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/groups/${id}`, { method: 'DELETE' }),
    addStudent: (groupId, payload) => request(`/schedules/groups/${groupId}/students`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },
  programmes: {
    list: (params) => request(`/schedules/programmes${toQuery(params)}`),
    get: (id) => request(`/schedules/programmes/${id}`),
    create: (payload) => request('/schedules/programmes', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/programmes/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/programmes/${id}`, { method: 'DELETE' })
  },
  courses: {
    list: (params) => request(`/schedules/courses${toQuery(params)}`),
    get: (id) => request(`/schedules/courses/${id}`),
    create: (payload) => request('/schedules/courses', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/courses/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/courses/${id}`, { method: 'DELETE' })
  },
  modules: {
    list: (params) => request(`/schedules/modules${toQuery(params)}`),
    get: (id) => request(`/schedules/modules/${id}`),
    create: (payload) => request('/schedules/modules', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/modules/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/modules/${id}`, { method: 'DELETE' })
  },
  academicYears: {
    list: (params) => request(`/schedules/academic-years${toQuery(params)}`),
    get: (id) => request(`/schedules/academic-years/${id}`),
    create: (payload) => request('/schedules/academic-years', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/academic-years/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/academic-years/${id}`, { method: 'DELETE' })
  },
  holidays: {
    list: (params) => request(`/schedules/holidays${toQuery(params)}`),
    get: (id) => request(`/schedules/holidays/${id}`),
    create: (payload) => request('/schedules/holidays', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schedules/holidays/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schedules/holidays/${id}`, { method: 'DELETE' })
  }
};

export { request };
