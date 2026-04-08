#!/bin/bash

# jmAgent Local Development Environment
# Manages backend and frontend processes

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
SHELL_DIR="$PROJECT_ROOT/shell"

# Process management
PID_DIR="$SHELL_DIR/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# Ports
BACKEND_PORT=6100
FRONTEND_PORT=6110

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Ensure PID directory exists
mkdir -p "$PID_DIR"

# Check if process is running
is_running() {
  local pid_file=$1
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

# Get process info
get_process_info() {
  local pid_file=$1
  if [ -f "$pid_file" ]; then
    cat "$pid_file"
  else
    echo "Not running"
  fi
}

# Start backend
start_backend() {
  if is_running "$BACKEND_PID_FILE"; then
    log_warn "Backend already running (PID: $(cat $BACKEND_PID_FILE))"
    return 0
  fi

  log_info "Starting backend on port $BACKEND_PORT..."
  cd "$BACKEND_DIR"

  python3 -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --reload \
    > "$SHELL_DIR/backend.log" 2>&1 &

  local backend_pid=$!
  echo $backend_pid > "$BACKEND_PID_FILE"

  # Wait for backend to be ready
  sleep 2

  if is_running "$BACKEND_PID_FILE"; then
    log_success "Backend started (PID: $backend_pid)"
    log_info "Backend URL: http://localhost:$BACKEND_PORT"
    return 0
  else
    log_error "Failed to start backend. Check logs:"
    cat "$SHELL_DIR/backend.log"
    rm -f "$BACKEND_PID_FILE"
    return 1
  fi
}

# Start frontend
start_frontend() {
  if is_running "$FRONTEND_PID_FILE"; then
    log_warn "Frontend already running (PID: $(cat $FRONTEND_PID_FILE))"
    return 0
  fi

  log_info "Starting frontend on port $FRONTEND_PORT..."
  cd "$FRONTEND_DIR"

  VITE_API_BASE_URL="http://localhost:$BACKEND_PORT/api/v1" \
  npm run dev \
    > "$SHELL_DIR/frontend.log" 2>&1 &

  local frontend_pid=$!
  echo $frontend_pid > "$FRONTEND_PID_FILE"

  # Wait for frontend to be ready
  sleep 3

  if is_running "$FRONTEND_PID_FILE"; then
    log_success "Frontend started (PID: $frontend_pid)"
    log_info "Frontend URL: http://localhost:$FRONTEND_PORT"
    return 0
  else
    log_error "Failed to start frontend. Check logs:"
    cat "$SHELL_DIR/frontend.log"
    rm -f "$FRONTEND_PID_FILE"
    return 1
  fi
}

# Stop backend
stop_backend() {
  if [ ! -f "$BACKEND_PID_FILE" ]; then
    log_warn "Backend not running"
    return 0
  fi

  local pid=$(cat "$BACKEND_PID_FILE")
  log_info "Stopping backend (PID: $pid)..."

  if kill -0 "$pid" 2>/dev/null; then
    kill $pid 2>/dev/null || true
    sleep 1

    if is_running "$BACKEND_PID_FILE"; then
      log_warn "Backend still running, force killing..."
      kill -9 $pid 2>/dev/null || true
      sleep 1
    fi
  fi

  rm -f "$BACKEND_PID_FILE"
  log_success "Backend stopped"
}

# Stop frontend
stop_frontend() {
  if [ ! -f "$FRONTEND_PID_FILE" ]; then
    log_warn "Frontend not running"
    return 0
  fi

  local pid=$(cat "$FRONTEND_PID_FILE")
  log_info "Stopping frontend (PID: $pid)..."

  if kill -0 "$pid" 2>/dev/null; then
    kill $pid 2>/dev/null || true
    sleep 1

    if is_running "$FRONTEND_PID_FILE"; then
      log_warn "Frontend still running, force killing..."
      kill -9 $pid 2>/dev/null || true
      sleep 1
    fi
  fi

  rm -f "$FRONTEND_PID_FILE"
  log_success "Frontend stopped"
}

# Show status
show_status() {
  echo ""
  echo -e "${BLUE}═══════════════════════════════════════${NC}"
  echo -e "${BLUE}  jmAgent Local Development Status${NC}"
  echo -e "${BLUE}═══════════════════════════════════════${NC}"

  echo ""
  echo "Backend:"
  if is_running "$BACKEND_PID_FILE"; then
    echo -e "  ${GREEN}✓ Running${NC} (PID: $(cat $BACKEND_PID_FILE))"
    echo -e "  🌐 http://localhost:$BACKEND_PORT"
  else
    echo -e "  ${RED}✗ Not running${NC}"
  fi

  echo ""
  echo "Frontend:"
  if is_running "$FRONTEND_PID_FILE"; then
    echo -e "  ${GREEN}✓ Running${NC} (PID: $(cat $FRONTEND_PID_FILE))"
    echo -e "  🌐 http://localhost:$FRONTEND_PORT"
  else
    echo -e "  ${RED}✗ Not running${NC}"
  fi

  echo ""
  echo "Logs:"
  echo -e "  📋 Backend:  $SHELL_DIR/backend.log"
  echo -e "  📋 Frontend: $SHELL_DIR/frontend.log"

  echo ""
  echo -e "${BLUE}═══════════════════════════════════════${NC}"
}

# Show logs
show_logs() {
  local service=$1

  case $service in
    backend)
      if [ -f "$SHELL_DIR/backend.log" ]; then
        echo -e "${BLUE}Backend Logs (last 30 lines):${NC}"
        tail -30 "$SHELL_DIR/backend.log"
      else
        log_warn "Backend log not found"
      fi
      ;;
    frontend)
      if [ -f "$SHELL_DIR/frontend.log" ]; then
        echo -e "${BLUE}Frontend Logs (last 30 lines):${NC}"
        tail -30 "$SHELL_DIR/frontend.log"
      else
        log_warn "Frontend log not found"
      fi
      ;;
    *)
      log_error "Unknown service: $service"
      echo "Usage: $0 logs {backend|frontend}"
      exit 1
      ;;
  esac
}

# Main command handler
case "${1:-help}" in
  start)
    log_info "Starting jmAgent development environment..."
    start_backend && start_frontend
    show_status
    ;;

  stop)
    log_info "Stopping jmAgent development environment..."
    stop_frontend && stop_backend
    show_status
    ;;

  restart)
    log_info "Restarting jmAgent development environment..."
    stop_frontend && stop_backend
    sleep 2
    start_backend && start_frontend
    show_status
    ;;

  status)
    show_status
    ;;

  logs)
    show_logs "${2:-backend}"
    ;;

  logs-backend)
    show_logs "backend"
    ;;

  logs-frontend)
    show_logs "frontend"
    ;;

  kill)
    log_warn "Force killing all processes..."
    pkill -f "uvicorn src.api.main" || true
    pkill -f "vite" || true
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
    log_success "All processes killed"
    ;;

  help)
    cat << EOF
${BLUE}jmAgent Local Development Control${NC}

Usage: $(basename "$0") {command}

Commands:
  ${GREEN}start${NC}          - Start both backend and frontend
  ${GREEN}stop${NC}           - Stop both backend and frontend
  ${GREEN}restart${NC}        - Restart both backend and frontend
  ${GREEN}status${NC}         - Show status of services
  ${GREEN}logs${NC} [service] - Show logs (backend|frontend)
  ${GREEN}logs-backend${NC}   - Show backend logs
  ${GREEN}logs-frontend${NC}  - Show frontend logs
  ${GREEN}kill${NC}           - Force kill all processes (emergency)
  ${GREEN}help${NC}           - Show this help message

Examples:
  $(basename "$0") start
  $(basename "$0") restart
  $(basename "$0") logs backend
  $(basename "$0") status

Environment:
  Backend Port:  $BACKEND_PORT
  Frontend Port: $FRONTEND_PORT
  Project Root:  $PROJECT_ROOT

EOF
    ;;

  *)
    log_error "Unknown command: $1"
    echo "Run '$(basename "$0") help' for usage information"
    exit 1
    ;;
esac
