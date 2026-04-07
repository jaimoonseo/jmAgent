# jmAgent Web Dashboard - Frontend

React + TypeScript + Vite frontend for the jmAgent personal Claude coding assistant.

## Overview

The frontend provides a web-based interface for interacting with jmAgent's REST API. It includes authentication (JWT tokens and API keys), code generation, refactoring, testing, and more.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Testing**: Vitest + React Testing Library
- **Notifications**: React Hot Toast
- **Syntax Highlighting**: highlight.js

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios API client with interceptors
│   │   └── endpoints.ts       # API endpoint helpers
│   ├── components/
│   │   ├── Header.tsx         # Navigation header
│   │   ├── Sidebar.tsx        # Navigation sidebar
│   │   └── LoadingSpinner.tsx # Loading indicator
│   ├── pages/
│   │   ├── LoginPage.tsx      # JWT/API Key login
│   │   ├── DashboardPage.tsx  # Main dashboard
│   │   └── NotFoundPage.tsx   # 404 page
│   ├── hooks/
│   │   ├── useAuth.ts         # Authentication hook
│   │   └── useApi.ts          # API call hook
│   ├── store/
│   │   └── authStore.ts       # Zustand auth state
│   ├── types/
│   │   ├── auth.ts            # Auth types
│   │   └── api.ts             # API types
│   ├── utils/
│   │   ├── constants.ts       # App constants
│   │   └── storage.ts         # localStorage helpers
│   ├── __tests__/             # Test files
│   ├── App.tsx                # Main app with routing
│   ├── main.tsx               # React entry point
│   ├── index.css              # Global styles
│   └── vite-env.d.ts          # Vite environment types
├── index.html                 # HTML entry point
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript config
├── vite.config.ts             # Vite config
├── vitest.config.ts           # Vitest config
├── tailwind.config.js         # Tailwind config
├── postcss.config.js          # PostCSS config
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm 9+
- Running jmAgent backend (http://localhost:8000)

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Update `.env` if using a different API base URL:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=jmAgent Web Dashboard
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at http://localhost:5173

### Building

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Authentication

The frontend supports two authentication methods:

### JWT Bearer Token

1. Go to the login page
2. Select "JWT Token" tab
3. Paste your JWT bearer token
4. Click "Sign In"

The token is stored in localStorage and sent with requests via `Authorization: Bearer <token>`

### API Key

1. Go to the login page
2. Select "API Key" tab
3. Paste your API key
4. Click "Sign In"

The API key is stored in localStorage and sent with requests via `X-API-Key: <key>`

## Features

### Dashboard
- Overview of activity statistics
- Feature shortcuts for quick access
- User profile information

### Code Generation
- Generate code from natural language descriptions
- Support for multiple programming languages

### Code Refactoring
- Improve existing code quality
- Add type hints, improve documentation
- Optimize performance

### Test Generation
- Automatically generate unit tests
- Support for pytest, vitest, jest, etc.

### Code Explanation
- Get detailed explanations of code
- Understand complex functions
- Learn best practices

### Bug Fixing
- Identify and fix bugs
- Error message interpretation
- Suggest improvements

## Testing

Run tests:

```bash
npm test
```

Run tests with UI:

```bash
npm run test:ui
```

Test files are located in `src/__tests__/` and use the `.test.ts` or `.test.tsx` extension.

## Styling

The frontend uses Tailwind CSS for styling. Customize by editing:

- `tailwind.config.js` - Tailwind configuration
- `src/index.css` - Global styles
- Component files - Component-specific styles

## API Integration

All API calls go through the axios client in `src/api/client.ts`. The client:

1. Adds authentication headers (Bearer token or API key)
2. Sets a 30-second timeout
3. Handles 401/403/500 errors with toast notifications
4. Auto-logs out on 401 (unauthorized)

Add new API endpoints in `src/api/endpoints.ts`:

```typescript
export const myApi = {
  myMethod: async (param: string) => {
    const response = await apiClient.post('/my-endpoint', { param })
    return response.data
  },
}
```

## Adding New Pages

1. Create the page component in `src/pages/`:

```typescript
export const MyPage = () => {
  return <div>My Page</div>
}
```

2. Add the route in `src/App.tsx`:

```typescript
<Route
  path="/my-page"
  element={
    <ProtectedRoute>
      <MyPage />
    </ProtectedRoute>
  }
/>
```

3. Add the navigation link in `src/components/Sidebar.tsx`:

```typescript
{ label: 'My Page', href: '/my-page', icon: '🎯' },
```

## Environment Variables

Available environment variables (see `.env.example`):

- `VITE_API_BASE_URL` - Backend API URL (default: http://localhost:8000/api/v1)
- `VITE_APP_TITLE` - Application title (default: jmAgent Web Dashboard)

## Performance Tips

1. **Code Splitting** - Routes are automatically code-split by Vite
2. **Lazy Loading** - Use React.lazy() for large components
3. **State Management** - Use Zustand for global state, minimize re-renders
4. **API Caching** - Consider adding response caching for repeated requests
5. **Image Optimization** - Use modern image formats and optimize dimensions

## Troubleshooting

### CORS Issues

If you see CORS errors, ensure:
1. Backend is running on http://localhost:8000
2. Backend has CORS headers configured correctly
3. API base URL in `.env` is correct

### Authentication Issues

If login fails:
1. Check the token/API key is valid
2. Ensure backend is running
3. Check browser console for detailed error messages

### Build Issues

Clear cache and reinstall:

```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Deployment

The production build is in the `dist/` directory. Deploy by:

1. Building the project: `npm run build`
2. Serving the `dist/` directory with a static file server
3. Configuring your server to serve `index.html` for all routes (SPA routing)

For Nginx:

```nginx
server {
  listen 80;
  root /path/to/dist;
  try_files $uri /index.html;
}
```

For Apache:

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

## Contributing

1. Create a new branch for your feature
2. Make changes following the existing code style
3. Write tests for new functionality
4. Run `npm test` to verify
5. Submit a pull request

## License

MIT - Same as jmAgent backend
