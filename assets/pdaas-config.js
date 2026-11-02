const siteBase = new URL('../', import.meta.url);
const apiBase = new URL('api/v1/', siteBase);

export const CONFIG = {
  API_BASE_URL: siteBase.origin,
  API_PREFIX: apiBase.pathname.replace(/\/$/, ''),
  KATALOG_ENDPOINT: '/katalog.json',
  LANG_STORAGE_KEY: 'pdaas_dil',
  PAGE_SIZE: 100,
};

export function resolveApiPath(path = '', siteRoot = siteBase) {
  const site = new URL(siteRoot);
  const apiRoot = new URL('api/v1/', site);
  const value = String(path).trim();
  if (/^https?:\/\//i.test(value)) return value;
  const normalized = value.replace(/^(?:\.\/)+/, '').replace(/^\/+/, '');
  const rootPrefix = site.pathname.replace(/^\/+|\/+$/g, '');
  const siteRelative = rootPrefix && normalized.startsWith(rootPrefix + '/')
    ? normalized.slice(rootPrefix.length + 1) : normalized;
  if (/^api\//i.test(siteRelative) || /^(?:assets|json)\//i.test(siteRelative)) {
    return new URL(siteRelative, site).href;
  }
  return new URL(siteRelative, apiRoot).href;
}

export function apiUrl(path = '') { return resolveApiPath(path); }

// Katalog eski dizin yolları içerirse, mevcut düz api/v1 dosyalarını da dene.
export function serviceUrlCandidates(service, layer, siteRoot = siteBase) {
  const url = service?.katmanlar?.[layer]?.url;
  if (!url) return [];
  const site = new URL(siteRoot);
  const original = resolveApiPath(url, site);
  const root = new URL('api/v1/', site);
  const target = new URL(original);
  if (target.origin !== site.origin || !/\.json$/i.test(target.pathname)) return [original];

  const kod = String(service.kod || '').trim();
  const ad = decodeURIComponent(target.pathname.split('/').pop() || '');
  const candidates = [];
  const add = name => {
    if (/^[a-z0-9][a-z0-9._-]*\.json$/i.test(name)) candidates.push(new URL(name, root).href);
  };
  if (layer === 'kurallar') add(kod.endsWith('-kurallar') ? `${kod}.json` : `${kod}-kurallar.json`);
  if (layer === 'konsolide') {
    add(`${kod}-tam.json`);
    if (kod === 'gtip-kodlari') add('gtip-tam.json');
  }
  if (ad !== 'index.json' && ad !== 'son.json') add(ad);
  add(`${kod}.json`);
  candidates.push(original);
  return [...new Set(candidates)];
}

export async function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), {
    ...options,
    headers: { Accept: 'application/json', ...(options.headers || {}) }
  });
}
