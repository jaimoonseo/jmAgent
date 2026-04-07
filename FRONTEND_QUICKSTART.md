# jmAgent Frontend - Quick Start Guide

## Overview

Professional React + TypeScript + Vite frontend for the jmAgent personal Claude coding assistant.

**Location**: `/Users/jaimoonseo/Documents/jmAgent/frontend/`

## Quick Commands

```bash
# Install dependencies
cd frontend
npm install

# Development (HMR enabled)
npm run dev
# -> http://localhost:5173

# Production build
npm run build
# -> dist/ folder

# Run tests
npm test
npm run test:ui

# Linting
npm run lint
```

## Project Features

- ✅ JWT Bearer token authentication
- ✅ API key authentication
- ✅ Protected routes with automatic logout on 401
- ✅ Zustand state management + localStorage persistence
- ✅ Axios HTTP client with auth interceptors
- ✅ Responsive Tailwind CSS design
- ✅ React Router v6 nested routing
- ✅ Vitest unit testing setup
- ✅ Type-safe TypeScript (strict mode)
- ✅ ESLint configuration
- ✅ Production build optimization

## File Structure

### Configuration
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript strict mode
- `vite.config.ts` - Vite with React plugin
- `tailwind.config.js` - Tailwind CSS theme
- `.env.example` - Environment variables

### Source Code
```
src/
├── api/           # HTTP client and endpoints
├── components/    # Reusable UI components
├── pages/         # Route components
├── hooks/         # Custom React hooks
├── store/         # Zustand state management
├── types/         # TypeScript interfaces
├── utils/         # Helper functions
├── __tests__/     # Unit tests
├── App.tsx        # Main app with routing
└── main.tsx       # React entry point
```

### Key Files

| File | Purpose |
|------|---------|
| `src/api/client.ts` | Axios with auth interceptors |
| `src/store/authStore.ts` | Zustand auth state |
| `src/hooks/useAuth.ts` | Authentication hook |
| `src/pages/LoginPage.tsx` | JWT/API key login |
| `src/App.tsx` | App routing and hydration |
| `vite.config.ts` | Dev proxy to backend |

## Authentication

### JWT Token Login
1. Go to http://localhost:5173/login
2. Select "JWT Token" tab
3. Paste token from backend
4. Click "Sign In"

### API Key Login
1. Go to http://localhost:5173/login
2. Select "API Key" tab
3. Paste API key from backend
4. Click "Sign In"

Token/key is stored in localStorage and sent with requests.

## API Integration

API base URL: `http://localhost:8000/api/v1` (configurable via `.env`)

Headers added automatically:
- `Authorization: Bearer <token>` (JWT)
- OR `X-API-Key: <key>` (API Key)

## Routes

| Path | Auth Required | Purpose |
|------|---------------|---------|
| `/login` | ❌ No | Login page |
| `/dashboard` | ✅ Yes | Main dashboard |
| `/*` | ❌ No | 404 page |

Protected routes redirect to login if not authenticated.

## Development Workflow

1. **Start backend**: `python src/cli.py` (or `npm run dev` in backend directory)
2. **Start frontend**: `cd frontend && npm run dev`
3. **Login** with JWT token or API key from backend
4. **Develop** with HMR enabled (changes auto-reload)

## Environment Variables

Create `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=jmAgent Web Dashboard
```

## Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with UI dashboard
npm run test:ui

# Coverage
npm test -- --coverage
```

## Building for Production

```bash
# Build
npm run build

# Preview production build
npm run preview
```

Output: `dist/` folder ready to serve

## Styling

Uses Tailwind CSS for all styling:
- Utility-first CSS framework
- Dark mode support ready (Phase 2)
- Mobile-first responsive design
- Custom color scheme (blues and slates)

Customize theme in `tailwind.config.js`

## Troubleshooting

### Port already in use
```bash
lsof -i :5173
kill <PID>
```

### CORS errors
- Ensure backend is running on http://localhost:8000
- Check `vite.config.ts` proxy settings
- Verify `VITE_API_BASE_URL` in `.env`

### Login fails
- Check token/API key validity
- Verify backend is running
- Check browser console for errors

### Build fails
```bash
rm -rf node_modules package-lock.json dist
npm install
npm run build
```

## Next Phase

Phase 5, Subtask 2 will add:
- Code generation page
- Refactoring page
- Test generation page
- Code explanation page
- Bug fixing page
- Chat interface
- WebSocket streaming
- Dark mode toggle

## Documentation

- **README.md** - Comprehensive guide
- **PROJECT_STRUCTURE.md** - File inventory
- **PHASE5_SUBTASK1_COMPLETION.md** - Full completion report

## Support

For issues or questions:
1. Check frontend README.md
2. Review error messages in browser console
3. Verify backend is running
4. Check `vite.config.ts` for proxy settings
