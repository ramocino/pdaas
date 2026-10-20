import { $ } from './pdaas-utils.js';
import { CONFIG } from './pdaas-config.js';

export const UI = {
  tr: {
    portal_alt: "Parametrik Veri Servisi Portalı",
    nav_portal: "Portal",
    nav_urunhizmetara: "Ürün & Hizmet Ara",
    nav_urunhizmetkarti: "Ürün & Hizmet Kartı",
    nav_personel: "Personel",
    nav_muhtasar: "Muhtasar",
    nav_konsolide: "Konsolide",
    system_active: "Sistem Aktif",
    copied: "Kopyalandı",
    copied_url: "Endpoint adresi kopyalandı",
    copied_code: "Hazır kod kopyalandı",
    copied_json: "JSON payload kopyalandı",
    error_copy: "Kopyalanamadı",
  },
  en: {
    portal_alt: "Parametric Data Service Portal",
    nav_portal: "Portal",
    nav_urunhizmetara: "Products & Services Search",
    nav_urunhizmetkarti: "Products & Services Card",
    nav_personel: "Personnel",
    nav_muhtasar: "Withholding",
    nav_konsolide: "Konsolide",
    system_active: "System Active",
    copied: "Copied",
    copied_url: "Endpoint URL copied",
    copied_code: "Code snippet copied",
    copied_json: "JSON payload copied",
    error_copy: "Copy failed",
  }
};

let DIL = 'tr';
export const getDil = () => DIL;

export function t(k) { return (UI[DIL] && UI[DIL][k]) || k; }

export function alanSec(obj, temelAd) {
  if (!obj) return '';
  const en = obj[temelAd + '_en'], tr = obj[temelAd + '_tr'], eski = obj[temelAd];
  if (DIL === 'en') return en || tr || eski || '';
  return tr || eski || en || '';
}
export function kayitAdi(k) {
  return alanSec(k, 'tanim') || alanSec(k, 'ad') || '—';
}
export function aciklamaAdi(o) { return alanSec(o, 'aciklama'); }

export function dilUygula() {
  document.documentElement.lang = DIL;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  const trBtn = $('lang-tr'), enBtn = $('lang-en');
  if (trBtn && enBtn) {
    trBtn.className = DIL === 'tr'
      ? 'px-2 lg:px-2.5 py-1 rounded bg-win-500 text-white transition'
      : 'px-2 lg:px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
    enBtn.className = DIL === 'en'
      ? 'px-2 lg:px-2.5 py-1 rounded bg-win-500 text-white transition'
      : 'px-2 lg:px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
  }
  try { localStorage.setItem(CONFIG.LANG_STORAGE_KEY, DIL); } catch (e) {}
}

export function dilDegistir(yeni) {
  if (yeni === DIL) return;
  DIL = yeni;
  dilUygula();
  document.dispatchEvent(new CustomEvent('pdaas:dil', { detail: { dil: DIL } }));
}

export function dilBaslat() {
  const q = new URLSearchParams(location.search).get('lang');
  if (q && ['tr', 'en'].includes(q)) { DIL = q; return; }
  try {
    const k = localStorage.getItem(CONFIG.LANG_STORAGE_KEY);
    if (k && ['tr', 'en'].includes(k)) DIL = k;
  } catch (e) {}
}

export function showToast(title, message, isError = false) {
  const toast = $('toast-notification');
  if (!toast) return;
  $('toast-title').textContent = title;
  $('toast-message').textContent = message;
  const icon = $('toast-icon');
  if (isError) {
    icon.className = 'w-7 h-7 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold text-sm';
    icon.textContent = '✕';
  } else {
    icon.className = 'w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm';
    icon.textContent = '✓';
  }
  toast.classList.remove('translate-y-20', 'opacity-0', 'pointer-events-none');
  setTimeout(() => toast.classList.add('translate-y-20', 'opacity-0', 'pointer-events-none'), 2500);
}

export function copyToClipboard(text, successMsg) {
  const ok = () => showToast(t('copied'), successMsg);
  const fail = () => showToast(t('error_copy'), '', true);
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(ok, fail);
  } else {
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); ok(); } catch (e) { fail(); }
    document.body.removeChild(ta);
  }
}