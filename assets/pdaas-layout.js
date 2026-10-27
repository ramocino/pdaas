import { $ } from './pdaas-utils.js';
import { dilDegistir } from './pdaas-i18n.js';

const NAV = [
  { href: 'index.html',           key: 'nav_portal' },
  { href: 'urunhizmetkarti.html', key: 'nav_urunhizmetkarti' },
  { href: 'muhtasar.html',        key: 'nav_muhtasar' },
];

export function renderLayout({ activePage = 'index.html' } = {}) {
  const slot = $('pdaas-header');
  if (!slot) return;

  const navDesktop = NAV.map(n => {
    const aktif = n.href === activePage;
    const cls = aktif
      ? 'px-3 py-1.5 rounded-md text-xs font-semibold text-white bg-win-hover border border-win-border'
      : 'px-3 py-1.5 rounded-md text-xs font-semibold text-slate-400 hover:text-white hover:bg-win-hover transition';
    return `<a href="${n.href}" class="${cls}" data-i18n="${n.key}"></a>`;
  }).join('');

  const navMobil = NAV.map(n => {
    const aktif = n.href === activePage;
    const cls = aktif
      ? 'block px-3 py-2.5 rounded-md text-sm font-bold text-white bg-win-hover border border-win-border'
      : 'block px-3 py-2.5 rounded-md text-sm font-bold text-slate-400 hover:text-white hover:bg-win-hover transition';
    return `<a href="${n.href}" class="${cls}" data-i18n="${n.key}"></a>`;
  }).join('');

  slot.outerHTML = `
    <header class="h-16 flex-none border-b border-win-border bg-win-dark/80 sticky top-0 z-40 mica-panel flex items-center justify-between px-3 sm:px-4 lg:px-6 gap-2">
      <div class="flex items-center gap-2 lg:gap-3 min-w-0 flex-1">
        <button id="btn-mobile-menu" type="button" class="lg:hidden p-2 text-slate-400 hover:text-white rounded-md hover:bg-win-hover transition flex-none" aria-label="Menü">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>

        <a href="index.html" class="flex items-center gap-3 flex-none min-w-0">
          <div class="w-9 h-9 rounded-md bg-win-500 flex items-center justify-center font-bold text-white text-lg flex-none">P</div>
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-bold text-sm sm:text-base tracking-tight text-white">PDaaS</span>
              <span class="text-[10px] font-semibold uppercase tracking-wider bg-win-500/20 text-win-400 px-1.5 sm:px-2 py-0.5 rounded border border-win-500/30 whitespace-nowrap">v1 API</span>
            </div>
            <p class="text-[10px] sm:text-xs text-slate-400 font-medium truncate" data-i18n="portal_alt"></p>
          </div>
        </a>

        <nav class="hidden lg:flex items-center gap-1 ml-4">${navDesktop}</nav>
      </div>

      <div class="flex items-center gap-2 lg:gap-3 flex-none">
        <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span data-i18n="system_active"></span>
        </div>
        <div class="flex items-center bg-win-card p-1 rounded-md border border-win-border text-xs font-semibold">
          <button id="lang-tr" type="button" class="px-2 lg:px-2.5 py-1 rounded text-slate-400 hover:text-white transition">TR</button>
          <button id="lang-en" type="button" class="px-2 lg:px-2.5 py-1 rounded bg-win-500 text-white transition">EN</button>
        </div>
      </div>
    </header>

    <div id="mobil-menu" class="hidden lg:hidden fixed top-16 left-0 right-0 z-[100] bg-win-dark/95 mica-panel border-b border-win-border p-3 space-y-1 shadow-2xl">
      ${navMobil}
    </div>
  `;

  $('lang-tr').addEventListener('click', () => dilDegistir('tr'));
  $('lang-en').addEventListener('click', () => dilDegistir('en'));

  const btnMobile = $('btn-mobile-menu');
  const mobilMenu = $('mobil-menu');
  btnMobile.addEventListener('click', e => { e.stopPropagation(); mobilMenu.classList.toggle('hidden'); });
  mobilMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mobilMenu.classList.add('hidden')));
  document.addEventListener('click', e => {
    if (!mobilMenu.classList.contains('hidden')
      && !mobilMenu.contains(e.target)
      && !btnMobile.contains(e.target)) {
      mobilMenu.classList.add('hidden');
    }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') mobilMenu.classList.add('hidden'); });
}