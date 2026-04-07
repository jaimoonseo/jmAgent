export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api/v1'
export const APP_TITLE = (import.meta.env.VITE_APP_TITLE as string) || 'jmAgent Web Dashboard'

export const AUTH_STORAGE_KEYS = {
  TOKEN: 'jmAgent:auth:token',
  API_KEY: 'jmAgent:auth:apiKey',
  USER: 'jmAgent:auth:user',
}

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500,
}

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  CONFIG: '/config',
  FILES: '/files',
  NOT_FOUND: '*',
}

export const AUTH_HEADERS = {
  BEARER: 'Bearer',
  API_KEY: 'X-API-Key',
}
