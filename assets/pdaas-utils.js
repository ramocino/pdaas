export const $ = id => document.getElementById(id);

export const kacis = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export const tr_lower = s => String(s ?? '').toLocaleLowerCase('tr-TR');
export const sayi = n => (n == null ? '—' : Number(n).toLocaleString('tr-TR'));
export const normKod = k => String(k ?? '').trim().replace(/\s+/g, '');
export const kodTemiz = k => normKod(k).replace(/\./g, '');

export function icNesneOzet(val) {
  if (Array.isArray(val)) {
    const n = val.length;
    if (n > 0 && typeof val[0] === 'object' && val[0] !== null) {
      const ilk = Object.entries(val[0]).slice(0, 2)
        .map(([k, v]) => `${k}: ${String(v).slice(0, 20)}`).join(' · ');
      return { label: `[${n}] ${ilk}`, title: JSON.stringify(val, null, 2) };
    }
    return { label: `[${n}]`, title: JSON.stringify(val, null, 2) };
  }
  const keys = Object.keys(val);
  const ozet = keys.slice(0, 3).map(k => `${k}: ${String(val[k]).slice(0, 20)}`).join(' · ');
  return { label: `{${keys.length}} ${ozet}`, title: JSON.stringify(val, null, 2) };
}

export function sayfaNumaralari(current, total) {
  const delta = 1; const range = []; const sonuc = [];
  for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) range.push(i);
  if (current - delta > 2) range.unshift('...left');
  if (current + delta < total - 1) range.push('...right');
  sonuc.push(1); sonuc.push(...range);
  if (total > 1) sonuc.push(total);
  return sonuc;
}