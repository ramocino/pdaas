import { apiUrl } from './pdaas-config.js';

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

/* Her iki sayfanın ortak ağ, dil ve güvenli gösterim yardımcıları. */

const TEXT = {
  tr: {
    catalog:'VERİ KATALOĞU',datasets:'Veri servisleri',searchService:'Kod veya servis adı...',loadingCatalog:'Katalog yükleniyor...',apiCatalog:'API v1 · Dinamik katalog',
    heroTitle:'Veriyi keşfedin.<br><span>Yapısını anlayın.</span>',heroDesc:'Ham kaynakları, eşleştirme kurallarını ve konsolide sonuçları tek bir katalogdan inceleyin. Her servis gerçek JSON dosyasına bağlanır.',browse:'Servislere göz at',openCards:'Ürün kartlarını aç ↗',introNote:'Katmanlar katalogdan otomatik belirlenir. JSON içeriğine veya metalarına müdahale edilmez.',
    backCatalog:'Katalog',endpoint:'API uç noktası',copyUrl:'Adresi kopyala',records:'Kayıt',updated:'Güncelleme',format:'Biçim',dataSections:'Veri bölümleri',sectionHelp:'Bir bölüm seçerek kayıtlarını inceleyebilirsiniz.',
    tabTable:'▦ Tablo',tabJson:'{ } JSON',tabCode:'⌘ Kod örnekleri',tabSchema:'◇ Alanlar',searchRows:'Tabloda ara...',csv:'CSV ↓',downloadJson:'JSON ↓',prev:'← Önceki',next:'Sonraki →',
    jsonPreview:'JSON önizleme',jsonNote:'Büyük dosyalarda ilk kayıtlar gösterilir; indirme tam bölümü içerir.',copyPreview:'Önizlemeyi kopyala',codeExamples:'Bağlantı kodları',copyCode:'Kodu kopyala',fieldDescription:'Alanlar ve türler',schemaInfo:'Kayıtlarda bulunan alanlardan oluşturulur.',field:'Alan',type:'Tür',example:'Örnek',
    loadingData:'Veriler okunuyor...',loading:'Yükleniyor...',layer_ham:'Ham veriler',layer_kurallar:'Eşleştirme kuralları',layer_konsolide:'Konsolide veriler',layer_ornek:'Örnekler',
    rows:'kayıt',page:'sayfa',of:'/',noRows:'Bu bölümde kayıt yok.',noMatches:'Eşleşme bulunamadı.',serviceUnavailable:'Dosya okunamadı. JSON yolu ve sunucu konumunu kontrol edin.',ready:'Bağlandı',copied:'Kopyalandı',copyFailed:'Kopyalama başarısız.',
    catalogEyebrow:'ÜRÜN & HİZMET',categories:'Kategoriler',categoryHelp:'Aramak veya incelemek istediğiniz kod türünü seçin.',publicBrowse:'Herkes için anlaşılır veri',eyebrow:'PDaaS · Veri keşfi',title:'Ürün veya hizmetinizi bulun.',
    subtitle:'GTİP kodunu yazın, ürün adını arayın veya sınıflandırmaların içinde ilerleyin. İlgili bilgiler tek bir kartta karşınıza gelsin.',searchPlaceholder:'Örn. 070410900000, buğday, tişört...',hint1:'Kod ve isimle arama',hint2:'Türkçe / English',hint3:'GTİP → CPC → NACE',results:'Kodlar ve sınıflandırmalar',back:'← Geri',loadMore:'Daha fazla göster',
    all:'Tümü',allDesc:'Bütün kod sistemleri',gtip:'GTİP',gtipDesc:'Ürün ve gümrük kodları',cpc:'CPC',cpcDesc:'Ürün / hizmet sınıfları',nace:'NACE',naceDesc:'Faaliyet kodları',isco:'ISCO',iscoDesc:'Meslek kodları',
    domestic:'Yurtiçi satış',import:'İthalat',export:'İhracat',tax:'Vergi bilgileri',documents:'Zorunlu belgeler ve izinler',general:'Genel bilgiler',classifications:'Sınıflandırma eşleşmeleri',relatedGtip:'İlişkili GTİP kodları',relatedCpc:'İlişkili CPC kodları',relatedNace:'İlişkili NACE kodları',yield:'Randıman / girdi–çıktı',
    turkish:'Türkçe adı',english:'İngilizce adı',unit:'Ölçü birimi',code:'Kod',parent:'Üst kod',noData:'—',taxNone:'Bu senaryoda tanımlı vergi bilgisi yok.',docNone:'Bu senaryoda tanımlı belge yok.',
    vat:'KDV',sct:'ÖTV',withholding:'Tevkifat',customs:'Gümrük vergisi',stamp:'Damga vergisi',exempt:'İstisna',conditional:'Koşullu',mandatory:'Zorunlu',optional:'İsteğe bağlı',application:'Uygulama',originAssumption:'Menşe varsayımı',buyer:'Alıcı',
    relatedHint:'Vergiler ve belgeler her bir GTİP kodunda farklı olabilir. Ayrıntıları görmek için GTİP seçin.',iscoHint:'ISCO bir meslek sınıflamasıdır. Bu kod için doğrudan GTİP vergisi veya gümrük belgesi gösterilmez.',
    moreRelated:'İlk 35 eşleşme gösteriliyor.',notAvailable:'İlgili eşleştirme bulunamadı.',searchHint:'Bir kod veya ürün adı yazabilirsiniz.',rootHint:'Bir kategori seçin veya kod ağacını genişletin.',unknown:'Bilinmiyor',scope:'Kapsam',condition:'Koşul',status:'Durum',
    demoNote:'Bu kart, PDaaS eşleştirme verilerinin örnek gösterimidir. Vergiler, istisnalar ve izinler işlem koşullarına göre ayrıca doğrulanmalıdır.'
  },
  en: {
    catalog:'DATA CATALOGUE',datasets:'Data services',searchService:'Search code or service...',loadingCatalog:'Loading catalogue...',apiCatalog:'API v1 · Dynamic catalogue',
    heroTitle:'Explore data.<br><span>Understand its structure.</span>',heroDesc:'Examine raw sources, mapping rules and consolidated outputs in a single catalogue. Each service connects to an actual JSON endpoint.',browse:'Browse services',openCards:'Explore product cards ↗',introNote:'Layers are determined automatically by the catalogue. JSON records and metadata are not modified.',
    backCatalog:'Catalogue',endpoint:'API endpoint',copyUrl:'Copy URL',records:'Records',updated:'Updated',format:'Format',dataSections:'Data sections',sectionHelp:'Select a section to inspect its records.',
    tabTable:'▦ Table',tabJson:'{ } JSON',tabCode:'⌘ Code examples',tabSchema:'◇ Fields',searchRows:'Search rows...',csv:'CSV ↓',downloadJson:'JSON ↓',prev:'← Previous',next:'Next →',
    jsonPreview:'JSON preview',jsonNote:'Large datasets show only initial records; downloads include the full selected section.',copyPreview:'Copy preview',codeExamples:'Integration examples',copyCode:'Copy code',fieldDescription:'Fields and types',schemaInfo:'Generated from actual record fields.',field:'Field',type:'Type',example:'Example',
    loadingData:'Loading data...',loading:'Loading...',layer_ham:'Raw datasets',layer_kurallar:'Mapping rules',layer_konsolide:'Consolidated datasets',layer_ornek:'Examples',
    rows:'records',page:'page',of:'/',noRows:'No records in this section.',noMatches:'No matching results.',serviceUnavailable:'File unavailable. Check the JSON path and server.',ready:'Connected',copied:'Copied',copyFailed:'Copy failed.',
    catalogEyebrow:'PRODUCTS & SERVICES',categories:'Categories',categoryHelp:'Choose the kind of codes you want to explore.',publicBrowse:'Accessible data for everyone',eyebrow:'PDaaS · Data explorer',title:'Find a product or service.',
    subtitle:'Search by GTİP code or product name, or browse the classification tree. Explore all related information in one card.',searchPlaceholder:'E.g. 070410900000, wheat, t-shirt...',hint1:'Search by name or code',hint2:'Turkish / English',hint3:'GTİP → CPC → NACE',results:'Codes and classifications',back:'← Back',loadMore:'Show more',
    all:'All',allDesc:'Every classification',gtip:'GTİP',gtipDesc:'Trade and product codes',cpc:'CPC',cpcDesc:'Product / service classes',nace:'NACE',naceDesc:'Activity codes',isco:'ISCO',iscoDesc:'Occupation codes',
    domestic:'Domestic sale',import:'Import',export:'Export',tax:'Tax information',documents:'Required documents & permits',general:'General information',classifications:'Classification mappings',relatedGtip:'Related GTİP codes',relatedCpc:'Related CPC codes',relatedNace:'Related NACE codes',yield:'Yield / input–output',
    turkish:'Turkish name',english:'English name',unit:'Unit of measure',code:'Code',parent:'Parent code',noData:'—',taxNone:'No tax data is defined for this scenario.',docNone:'No document is defined for this scenario.',
    vat:'VAT',sct:'SCT',withholding:'VAT withholding',customs:'Customs duty',stamp:'Stamp duty',exempt:'Exemption',conditional:'Conditional',mandatory:'Required',optional:'Optional',application:'Application',originAssumption:'Assumed origin',buyer:'Buyer',
    relatedHint:'Tax rates and documents may vary for each GTİP code. Select a GTİP to see its details.',iscoHint:'ISCO classifies occupations. No customs duties or product permits are assigned directly to an ISCO code.',
    moreRelated:'Showing the first 35 linked codes.',notAvailable:'No mapping is available.',searchHint:'Enter a code or product name.',rootHint:'Select a category or browse the classification tree.',unknown:'Unknown',scope:'Scope',condition:'Condition',status:'Status',
    demoNote:'This card demonstrates PDaaS mappings. Tax rates, exemptions and permits must be verified against the conditions of each transaction.'
  }
};

export const lang = () => document.documentElement.lang === 'en' ? 'en' : 'tr';
export const tx = key => TEXT[lang()]?.[key] ?? TEXT.tr[key] ?? key;
export const el = id => document.getElementById(id);
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const loc = (value, fallback = '') => typeof value === 'object' && value !== null && !Array.isArray(value)
  ? [value[lang()],value.tr,value.en].find(item=>item!==undefined && item!==null && item!=='') ?? fallback : (value ?? fallback);
export const nameOf = record => loc({tr:record?.ad_tr || record?.tanim_tr || record?.baslik_tr || record?.aciklama_tr,
  en:record?.ad_en || record?.tanim_en || record?.baslik_en || record?.aciklama_en}, '—') || '—';
export const normalize = text => String(text ?? '').toLocaleLowerCase('tr-TR').replaceAll('ı','i').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
export const number = value => value!==null && value!==undefined && value!=='' && Number.isFinite(+value) ? Number(value).toLocaleString(lang() === 'tr' ? 'tr-TR':'en-US') : '—';
export const percent = value => typeof value === 'number' ? `%${(value*100).toLocaleString(lang() === 'tr'?'tr-TR':'en-US',{maximumFractionDigits:4})}` : null;
export const isObject = item => item !== null && typeof item === 'object' && !Array.isArray(item);
export const json = value => JSON.stringify(value, null, 2);

const cache = new Map();
export function fetchJson(path) {
  const url = apiUrl(path);
  if (!cache.has(url)) {
    const promise = fetch(url, {headers:{Accept:'application/json'}}).then(async response => {
      if (!response.ok) throw new Error(`HTTP ${response.status} — ${new URL(url).pathname}`);
      const type = response.headers.get('content-type') || '';
      if (type && !/json|octet-stream|text\/plain/i.test(type)) throw new Error(`JSON olmayan yanıt (${type})`);
      return response.json();
    }).catch(error => {cache.delete(url);throw error;});
    cache.set(url, promise);
  }
  return cache.get(url);
}

export async function copyText(value) {
  try {
    if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(String(value));
    else {
      const area = document.createElement('textarea'); area.value = String(value);
      area.style.position = 'fixed'; area.style.opacity = '0';document.body.append(area);area.select();
      if (!document.execCommand('copy')) throw new Error('clipboard');area.remove();
    }
    notice(tx('copied'));
  } catch (error) { notice(tx('copyFailed'), true); }
}

let noticeTimeout;
export function notice(message, error = false) {
  const toast = el('toast-notification');if (!toast) return;
  el('toast-message').textContent = message;el('toast-icon').textContent = error ? '!' : '✓';
  toast.style.borderColor = error ? '#b46b6b' : '#477b6a';toast.classList.add('show');
  clearTimeout(noticeTimeout);noticeTimeout = setTimeout(() => toast.classList.remove('show'), 3200);
}

export function downloadFile(filename, body, mime = 'application/json;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([body],{type:mime}));
  const anchor = document.createElement('a');anchor.href = url;anchor.download = filename;
  document.body.appendChild(anchor);anchor.click();anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

export function initPage(activePage, selector) {
  void activePage; // Düzen ve dil HTML modülünde başlatılır.
  const translate = () => {
    document.querySelectorAll(selector).forEach(node => {
      const key = node.getAttribute(selector.slice(1,-1));
      if (key === 'heroTitle') node.innerHTML = tx(key);
      else node.textContent = tx(key);
    });
    document.querySelectorAll('[data-placeholder],[data-card-placeholder]').forEach(node => {
      node.placeholder = tx(node.dataset.placeholder || node.dataset.cardPlaceholder);
    });
    document.querySelectorAll('[data-ui-title]').forEach(node => node.title = tx(node.dataset.uiTitle));
  };
  translate();document.addEventListener('pdaas:dil', translate);
  return translate;
}
