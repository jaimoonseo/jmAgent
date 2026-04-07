# jmAgent Web Dashboard - Quick Start Guide

## Installation & Setup

```bash
# Navigate to frontend directory
cd /Users/jaimoonseo/Documents/jmAgent/frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

The dashboard will be available at **http://localhost:5173**

## Development

### Running the Dev Server
```bash
npm run dev
```
- Hot reload enabled
- Runs on http://localhost:5173
- Connects to backend at http://localhost:8000/api/v1

### Running Tests
```bash
# Watch mode (re-runs on file changes)
npm test

# Single run
npm test -- --run

# UI mode
npm test -- --ui
```

### Building for Production
```bash
npm run build        # TypeScript + Vite build
npm run preview      # Preview production build
```

## Available Pages

| Page | URL | Icon | Purpose |
|------|-----|------|---------|
| Dashboard | `/dashboard` | 📊 | Overview and stats |
| Generate Code | `/generate` | ✨ | Create code from prompt |
| Refactor | `/refactor` | 🔧 | Improve existing code |
| Generate Tests | `/test` | 🧪 | Create unit tests |
| Explain Code | `/explain` | 📖 | Understand code |
| Bug Fix | `/fix` | 🐛 | Fix errors |
| Chat | `/chat` | 💬 | Interactive conversation |

## How to Use Each Page

### Generate Code (`/generate`)
1. Enter a description of what you want to create
2. Select a model (Haiku, Sonnet, or Opus)
3. Adjust temperature (0-1) and max tokens if needed
4. Click "Generate Code"
5. Copy the output or clear to start over

### Refactor Code (`/refactor`)
1. Paste code or upload a file
2. Enter refactoring requirements
3. Select model and parameters
4. Click "Refactor Code"
5. Review changes summary and refactored code

### Generate Tests (`/test`)
1. Paste code or upload a file
2. Select test framework (pytest, vitest, or jest)
3. Click "Generate Tests"
4. Review generated tests and coverage estimate

### Explain Code (`/explain`)
1. Paste code or upload a file
2. (Optional) Specify a focus area
3. Select explanation language (English or Korean)
4. Click "Explain Code"
5. Read explanation and key concepts

### Bug Fix (`/fix`)
1. Paste code or upload a file
2. Enter the error message
3. Click "Fix Bug"
4. Review fixed code and explanation

### Chat (`/chat`)
1. (Optional) Select model and max tokens before first message
2. Type your message
3. Press Enter to send (or Shift+Enter for new line)
4. Continue conversation
5. Click "New Chat" to reset conversation

## Features

### Syntax Highlighting
- Code output automatically highlighted
- Supports Python, JavaScript, TypeScript, SQL, Bash, JSON, etc.
- Dark theme (Atom One Dark)

### File Upload
- Drag and drop files into any input box
- Supported formats: .py, .ts, .js, .sql, .sh, .json, .yaml, .yml
- Max file size: 1MB

### Copy to Clipboard
- Click "Copy" button on any code output
- Automatic success notification
- Works on all major browsers

### Execution Stats
- Token count (input + output)
- Execution time in seconds
- Cost estimation (based on Haiku pricing)

### Responsive Design
- Mobile: Single column layout
- Tablet: 1.5 column layout
- Desktop: 2 column layout with wide panels

## Backend Requirements

The backend must have these endpoints:

```
POST /api/v1/agent/generate
POST /api/v1/agent/refactor
POST /api/v1/agent/test
POST /api/v1/agent/explain
POST /api/v1/agent/fix
POST /api/v1/agent/chat
```

Example request body for Generate:
```json
{
  "prompt": "Create a hello world function",
  "model": "haiku",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

## Authentication

The app uses either JWT Bearer tokens or API Keys:

1. **JWT Token**: Set in localStorage as `jmAgent:auth:token`
2. **API Key**: Set in localStorage as `jmAgent:auth:apiKey`

Both are sent with every API request via:
- Bearer token: `Authorization: Bearer <token>`
- API key: `X-API-Key: <key>`

## Troubleshooting

### Port 5173 Already in Use
```bash
# Kill the process on port 5173
lsof -ti:5173 | xargs kill -9
npm run dev
```

### Tests Failing
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm test
```

### Build Errors
```bash
# Check TypeScript compilation
npx tsc --noEmit

# Check Vite build
npm run build
```

### API Connection Issues
1. Verify backend is running on http://localhost:8000
2. Check VITE_API_BASE_URL in .env file
3. Check browser console for CORS errors
4. Verify auth token/API key is valid

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Send Chat Message | Enter |
| New Line in Chat | Shift+Enter |
| Focus Input | Tab |

## File Structure

```
frontend/
├── src/
│   ├── pages/          # Page components (6 new)
│   ├── components/     # Reusable components (5 new)
│   ├── hooks/          # Custom hooks (1 new)
│   ├── types/          # TypeScript types
│   ├── api/            # API integration
│   ├── __tests__/      # Test files
│   └── App.tsx         # Router setup
├── package.json
├── vite.config.ts
└── vitest.config.ts
```

## Dependencies

Key packages:
- **react** - UI framework
- **react-router-dom** - Routing
- **axios** - HTTP client
- **zustand** - State management
- **tailwindcss** - Styling
- **react-hot-toast** - Notifications
- **highlight.js** - Syntax highlighting

## Environment Variables

```bash
# .env file (optional)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=jmAgent Web Dashboard
```

## Performance Tips

1. **Model Selection**: Use Haiku for speed, Opus for quality
2. **Token Limits**: Lower max_tokens for faster responses
3. **Temperature**: Use 0.2 for consistency, higher for creativity
4. **Large Files**: Keep under 1MB for best performance

## Support

For issues or questions:
1. Check browser console for errors
2. Verify backend is running and responding
3. Check test files for examples: `src/__tests__/`
4. Review IMPLEMENTATION_SUMMARY.md for architecture

## Version Info

- **Frontend Version**: 1.0.0
- **Node Version**: 16+
- **React Version**: 18.2.0
- **TypeScript Version**: 5.3.0
- **Status**: Production Ready ✅

---

**Last Updated**: April 6, 2026
