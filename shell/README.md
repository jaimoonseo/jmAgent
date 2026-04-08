# jmAgent Local Development Scripts

This directory contains scripts for managing the jmAgent development environment.

## Quick Start

```bash
# Start both backend and frontend
./local-start.sh start

# Check status
./local-start.sh status

# Stop services
./local-start.sh stop

# Restart services
./local-start.sh restart
```

## Commands

### `start`
Starts both backend (port 6100) and frontend (port 6110) services.

```bash
./local-start.sh start
```

✅ **Backend**: http://localhost:6100  
✅ **Frontend**: http://localhost:6110

---

### `stop`
Gracefully stops both backend and frontend services.

```bash
./local-start.sh stop
```

---

### `restart`
Restarts both backend and frontend services (stops then starts).

```bash
./local-start.sh restart
```

---

### `status`
Shows the current status of backend and frontend services.

```bash
./local-start.sh status
```

Example output:
```
✓ Backend Running (PID: 3819)
✓ Frontend Running (PID: 3846)
```

---

### `logs [service]`
Shows logs for a specific service (backend or frontend).

```bash
# Show backend logs
./local-start.sh logs backend

# Show frontend logs
./local-start.sh logs frontend

# Show last 50 lines
./local-start.sh logs backend | tail -50
```

---

### `logs-backend`
Shortcut for showing backend logs.

```bash
./local-start.sh logs-backend
```

---

### `logs-frontend`
Shortcut for showing frontend logs.

```bash
./local-start.sh logs-frontend
```

---

### `kill`
Force kills all processes (emergency stop if normal stop doesn't work).

```bash
./local-start.sh kill
```

---

### `help`
Shows help message with all available commands.

```bash
./local-start.sh help
```

---

## Setup (One-time)

### Option 1: Use full path
```bash
./shell/local-start.sh start
```

### Option 2: Create alias in shell profile
Add to your `~/.zshrc` or `~/.bash_profile`:

```bash
alias jm-dev='~/Documents/jmAgent/shell/local-start.sh'
```

Then reload:
```bash
source ~/.zshrc
```

Now use:
```bash
jm-dev start
jm-dev status
```

### Option 3: Add to PATH (requires sudo)
```bash
sudo ln -sf ~/Documents/jmAgent/shell/local-start.sh /usr/local/bin/jm-dev
```

Then use from anywhere:
```bash
jm-dev start
```

---

## Environment Configuration

The script automatically configures:

- **Backend Port**: 6100
- **Frontend Port**: 6110
- **API URL**: `http://localhost:6100/api/v1`

These are configured in the script and can be modified by editing `local-start.sh`.

---

## Logs

All logs are saved in this directory:

- `backend.log` - Backend (uvicorn) logs
- `frontend.log` - Frontend (vite) logs

View logs:
```bash
tail -f shell/backend.log    # Follow backend logs
tail -f shell/frontend.log   # Follow frontend logs
```

---

## Process Management

The script uses PID files to track processes:

- `.pids/backend.pid` - Backend process ID
- `.pids/frontend.pid` - Frontend process ID

These are automatically cleaned up when services are stopped.

---

## Troubleshooting

### Backend won't start
1. Check if port 6100 is already in use:
   ```bash
   lsof -i :6100
   ```
2. View backend logs:
   ```bash
   ./local-start.sh logs-backend
   ```
3. Force kill lingering processes:
   ```bash
   pkill -f uvicorn
   ```

### Frontend won't start
1. Check if port 6110 is already in use:
   ```bash
   lsof -i :6110
   ```
2. View frontend logs:
   ```bash
   ./local-start.sh logs-frontend
   ```
3. Force kill lingering processes:
   ```bash
   pkill -f vite
   ```

### Emergency stop
If services won't stop gracefully:
```bash
./local-start.sh kill
```

---

## Features

✅ **Automatic startup** - Both services start in background  
✅ **Process tracking** - Uses PID files for reliable management  
✅ **Log management** - Separate log files for each service  
✅ **Status checking** - Easy status verification  
✅ **Graceful shutdown** - Clean service shutdown with timeout  
✅ **Force kill** - Emergency termination if needed  
✅ **Color output** - Easy to read status messages  
✅ **Auto-detect failures** - Checks if services started successfully  

---

## Development Workflow

```bash
# 1. Start services
./local-start.sh start

# 2. Check status
./local-start.sh status

# 3. View logs while developing
./local-start.sh logs-backend

# 4. When done, stop services
./local-start.sh stop
```

---

## Integration with IDEs

### VS Code
Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start jmAgent Dev",
      "type": "shell",
      "command": "${workspaceFolder}/shell/local-start.sh",
      "args": ["start"],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Stop jmAgent Dev",
      "type": "shell",
      "command": "${workspaceFolder}/shell/local-start.sh",
      "args": ["stop"],
      "problemMatcher": []
    }
  ]
}
```

Then run tasks with `Cmd+Shift+P` → "Run Task".

---

## Notes

- Services run in background - the script returns immediately
- To follow logs in real-time, use: `tail -f shell/backend.log`
- Both services auto-reload on file changes (development mode)
- Frontend is configured to use `http://localhost:6100/api/v1` for API calls
