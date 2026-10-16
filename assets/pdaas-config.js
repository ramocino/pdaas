export const CONFIG = {
  API_BASE_URL: window.location.origin,
  KATALOG_ENDPOINT: '/api/v1/katalog.json',
  LANG_STORAGE_KEY: 'pdaas_dil',
  PAGE_SIZE: 100,
};

export function apiUrl(path) {
  const base = CONFIG.API_BASE_URL.replace(/\/+$/, '');
  const p = (path || '').startsWith('/') ? path : '/' + (path || '');
  return base + p;
}

export async function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), {
    ...options,
    headers: { 'Accept': 'application/json', ...(options.headers || {}) }
  });
}