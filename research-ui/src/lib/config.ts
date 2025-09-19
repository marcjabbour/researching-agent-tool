// Configuration for API endpoints
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000';

// Helper function to build API URLs
export const buildApiUrl = (path: string) => `${API_BASE_URL}${path}`;
export const buildWsUrl = (path: string) => `${WS_BASE_URL}${path}`;