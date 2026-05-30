# Frontend

Vite React frontend for the HSE classroom schedule and booking system.

## Structure

- `src/pages/` - route pages.
- `src/components/` - shared layout, widgets, modals, skeletons, and tables.
- `src/utils/` - API client, role access helpers, storage helpers, and mock fallbacks.
- `src/assets/` - HSE logo images and fonts.

## Configuration

The frontend reads `VITE_API_URL`, defaulting to `/api/v1` for Docker. Nginx proxies
that path to the gateway container.

## Docker

The frontend `Dockerfile` builds the Vite app with Node and serves the static output
with Nginx.
