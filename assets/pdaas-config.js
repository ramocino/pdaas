export const CONFIG = {
  API_BASE_URL: window.location.origin,
  // DİKKAT: Buraya /api/v2 ekledik
  API_PREFIX: '/pdaas/api/v2', 
  // KATALOG_ENDPOINT'ten /api/v2'yi kaldırdık (çünkü prefix zaten ekliyor)
  KATALOG_ENDPOINT: '/katalog.json', 
  LANG_STORAGE_KEY: 'pdaas_dil',
  PAGE_SIZE: 100,
};

export function apiUrl(path) {
  const base = CONFIG.API_BASE_URL.replace(/\/+$/, '');
  const prefix = CONFIG.API_PREFIX.replace(/\/+$/, '');
  
  let cleanPath = (path || '').startsWith('/') ? path : '/' + (path || '');
  if (prefix && !cleanPath.startsWith(prefix)) {
    cleanPath = prefix + cleanPath;
  }
  
  return base + cleanPath;
}

export async function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), {
    ...options,
    headers: { 'Accept': 'application/json', ...(options.headers || {}) }
  });
}