export const CONFIG = {
  API_BASE_URL: window.location.origin,
  
  API_PREFIX: window.location.pathname.replace(/\/[^\/]*\.html$/, '').replace(/\/$/, '') + '/api/v1',
  
  KATALOG_ENDPOINT: '/katalog.json', // apiUrl fonksiyonu başına prefix'i otomatik ekleyecek
  
  LANG_STORAGE_KEY: 'pdaas_dil',
  PAGE_SIZE: 100,
};

export function apiUrl(path) {
  const base = CONFIG.API_BASE_URL.replace(/\/+$/, '');
  
  if (path && path.startsWith('http')) return path;

  const prefix = CONFIG.API_PREFIX;
  let cleanPath = (path || '').startsWith('/') ? path : '/' + (path || '');
  
  if (cleanPath.startsWith('/api/v2')) {
     cleanPath = cleanPath.replace('/api/v2', '');
  }

  return base + prefix + cleanPath;
}

export async function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), {
    ...options,
    headers: { 'Accept': 'application/json', ...(options.headers || {}) }
  });
}