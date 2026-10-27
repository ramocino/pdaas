import { $ } from './pdaas-utils.js';
import { CONFIG } from './pdaas-config.js';

export const UI = {
  tr: {
    portal_alt: "Parametrik Veri Servisi Portalı",
    nav_portal: "Portal",
    nav_urunhizmetara: "Ürün & Hizmet Ara",
    nav_urunhizmetkarti: "Ürün & Hizmet Kartı",
    nav_muhtasar: "Muhtasar",
    nav_konsolide: "Konsolide",
    system_active: "Sistem Aktif",
    copied: "Kopyalandı",
    copied_url: "Endpoint adresi kopyalandı",
    copied_code: "Hazır kod kopyalandı",
    copied_json: "JSON payload kopyalandı",
    error_copy: "Kopyalanamadı",
    live_connection: "Canlı Bağlantı",
    back_to_list: "Listeye Dön",
    sgk_prim_baslik: "SGK Prim ve Teşvik Bilgileri",
    sgk_isci_payi: "İşçi Payı",
    sgk_sabit: "Sabit",
    sgk_isci_aciklama: "SGK + İşsizlik Sigortası",
    sgk_isveren_tevkisiz: "İşveren Payı (Teşviksiz)",
    sgk_standart_oran: "Standart oran",
    sgk_isveren_tevkisli: "İşveren Payı (Teşvikli)",
    sgk_indirimli: "İndirimli",
    sgk_tesvik_imalat: "5510 — Beş Puanlık Prim İndirimi (İmalat)",
    sgk_tesvik_diger: "5510 — İki Puanlık Prim İndirimi (İmalat Dışı)",

    // Katalog & Genel
    catalog_title: "Veri Kataloğu", catalog_search: "Veri seti ara...", catalog_loading: "Katalog yükleniyor...",
    empty_title: "Veri Seti veya Servis Seçin", empty_desc: "Sol taraftaki katalog ağacından bir veri seti seçerek, altındaki parametrik API servis uç noktalarını, veri tablolarını ve hazır kod örneklerini inceleyebilirsiniz.",
    empty_card1_t: "Veri Önizleme", empty_card1_d: "Tablo görünümü ile doğrudan canlı veri kayıtları.", empty_card2_t: "Hazır Kodlar", empty_card2_d: "cURL, Python, JS, Go & PHP entegrasyonu.",
    bc_home: "Katalog", run_query: "Yenile", endpoint_label: "API Uç Noktası", copy: "Kopyala", copy_payload: "Payload'ı Kopyala",
    tab_table: "Veri Tablosu", tab_code: "Bağlantı Kodları", tab_json: "JSON Konsolu", tab_docs: "Şema Dokümantasyonu",
    table_filter: "Tabloda filtrele...", page_label: "kayıt", page_of: "/", prev_page: "Önceki sayfa", next_page: "Sonraki sayfa",
    docs_title: "Veri Alanları ve Veri Tipleri", docs_field: "Alan Adı", docs_type: "Veri Tipi", docs_example: "Örnek", docs_desc: "Açıklama",
    records: "Kayıt", services: "Veri Seti", loading_data: "Veriler yükleniyor...", load_error: "Veri alınamadı. Endpoint yanıt vermedi.",
    filtered: "filtrelendi", filtered_none: "Filtreye uygun kayıt bulunamadı", no_records: "Kayıt bulunamadı", no_matches: "Eşleşen veri seti bulunamadı.",
    notlar_title: "Bilgi Notları",
    layer_ham: "Ham", layer_konsolide: "Konsolide", layer_kurallar: "Kural",

    // Ürün Kartı
    sayfa_baslik: "Ürün & Hizmet Kartı",
    sayfa_aciklama: "Kaynak türüne göre kart üretilir: GTİP (Ürün), CPC (Hizmet), NACE (Faaliyet), ISCO (Meslek).",
    arama_yer: "Ürün/hizmet adı, kod veya GTİP/CPC/NACE/ISCO ara…",
    filtre_hepsi: "Tümü", kategoriler_title: "Kategoriler", kategoriler_desc: "Kaynak türüne göre filtreleyin",
    kategori_hepsi_desc: "Tüm kaynaklar", kategori_gtip_desc: "Ürünler (KDV + ÖTV)", kategori_cpc_desc: "Hizmetler (KDV)", kategori_nace_desc: "Faaliyet sınıfları", kategori_isco_desc: "Meslek sınıfları",
    bos_baslik: "Aramaya başlayın", bos_aciklama: "Yukarıdaki arama kutusuna yazın; sonuçlar listede görünür. Bir kayda tıkladığınızda detay kartı açılır.",
    yukleniyor: "Veriler yükleniyor…", yuklendi: "Veriler hazır", yukleme_hatasi: "Veri kaynakları yüklenemedi",
    sonuc_yok_b: "Sonuç bulunamadı", sonuc_yok_p: "Farklı bir kelime veya kod deneyin.",
    satir: "satır", agac_gorunumu: "ağaç görünümü", baglam_not: "Soluk satırlar bağlam · Koyu satırlar arama eşleşmesi",
    kod_baslik: "Kodları", kapat: "Kapat",
    kart_urun: "Ürün Kartı", kart_hizmet: "CPC Kartı", kart_faaliyet: "Faaliyet Kartı", kart_meslek: "Meslek Kartı",
    kart_urun_desc: "Fiziki mal — KDV ve ÖTV'ye tabidir", kart_hizmet_desc: "CPC Sınıflandırması (Ürün veya Hizmet)", kart_faaliyet_desc: "Sektör/faaliyet kodu — vergi dışıdır", kart_meslek_desc: "Meslek sınıflaması — vergi dışıdır",
    alan_adi: "Standart Alan Adı", deger: "Değer / Standart", kurum: "Sorumlu Kurum", vergi: "Vergi Bilgileri",
    kdv_orani: "KDV Oranı", otv_orani: "ÖTV Oranı", kdv_yok: "Bu kayıt KDV'ye tabi değildir", otv_yok: "Bu kayıt ÖTV'ye tabi değildir", otv_muaf: "Muaf", muaf: "Muaf",
    kdv_listesi: "Liste", kdv_genel: "Genel Oran", kdv_tevkifat_oran: "KDV Tevkifat Oranı", kdv_tevkifat: "KDV Tevkifatı", uygulanmaz: "Uygulanmaz",
    tevkifat_uyari: "Alıcı-satıcı ilişkisine göre teyit edilmeli", tevkifat_satici_beyan: "KDV'nin tamamı satıcı tarafından beyan edilir",
    hizmet_otv_aciklama: "Hizmetler yalnızca KDV'ye tabidir",
    gtip_kod: "GTİP Kodu", cpc_kod: "CPC Kodu", nace_kod: "NACE Kodu", isco_kod: "ISCO Kodu",
    urun_ad_tr: "Ürün Adı (TR)", urun_ad_en: "Ürün Adı (EN)", hizmet_ad_tr: "Hizmet Adı (TR)", hizmet_ad_en: "Hizmet Adı (EN)",
    faaliyet_ad_tr: "Faaliyet Adı (TR)", faaliyet_ad_en: "Faaliyet Adı (EN)", meslek_ad_tr: "Meslek Adı (TR)", meslek_ad_en: "Meslek Adı (EN)",
    olcu_birimi: "Ölçü Birimi", seviye: "Hiyerarşi Seviyesi", seviye_adi: "Seviye Adı", ust_kod: "Üst Kod",
    zorunlu_standart: "Zorunlu Standart Kodu", tolerans: "Tolerans / Sapma Limiti (%)", tehlike_sinifi: "Tehlike Sınıfı", zorunlu_sigorta: "Zorunlu Sigorta",
    gorev_tanimi: "Görev Tanımı", beceri_seviyesi: "Beceri Seviyesi",
    belge_baslik: "Zorunlu Belgeler ve İzinler", belge_yok: "Bu kayıt için tanımlanmış belge bulunamadı", belge_zorunlu: "ZORUNLU", belge_kosullu: "KOŞULLU", belge_opsiyonel: "OPSİYONEL",
    randiman_baslik: "Fire ve Randıman Oranları", randiman_oran: "Randıman", fire_oran: "Fire", verimlilik_baslik: "Hizmet Verimlilik Göstergeleri", hedef_deger: "Hedef",
    vergi_disi_aciklama: "Sektör/meslek kodu — KDV/ÖTV konusu değildir",
    filtre_notu_urun: "Ürün kayıtları (GTİP): KDV ve ÖTV gösterilir.", filtre_notu_hizmet: "Hizmet kayıtları (CPC): KDV gösterilir; ÖTV uygulanmaz.",
    filtre_notu_nace: "NACE sektör kodları: vergi bilgisi yoktur.", filtre_notu_isco: "ISCO meslek kodları: vergi bilgisi yoktur.",
    kurum_tuik: "TÜİK", kurum_ticaret: "Ticaret Bakanlığı", kurum_gib: "GİB", kurum_tse: "TSE", kurum_calisma: "Çalışma Bakanlığı", kurum_tobb: "TOBB", kurum_seddk: "SEDDK", kurum_isg: "İSGGM",
    islem_tipleri: "İşlem Tipi", alici_tipleri: "Alıcı Tipi", satici_tipleri: "Satıcı Tipi", istisna: "İstisna Durumu", istisna_var: "İstisna Uygulanır", istisna_yok: "İstisna Yok", ek_kriterler: "Ek Kriterler",
    islem_yurtici: "Yurtiçi Satış", islem_ihracat: "İhracat (Yurtdışı)", islem_ithalat: "İthalat",
    tip_kamu: "Kamu Kurumu", tip_sirket: "Özel Sektör (Şirket)", tip_sahis: "Nihai Tüketici / Şahıs", tip_hepsi: "Tüm Alıcılar"
  },
  en: {
    portal_alt: "Parametric Data Service Portal",
    nav_portal: "Portal",
    nav_urunhizmetara: "Products & Services Search",
    nav_urunhizmetkarti: "Products & Services Card",
    nav_muhtasar: "Withholding",
    nav_konsolide: "Konsolide",
    system_active: "System Active",
    copied: "Copied",
    copied_url: "Endpoint URL copied",
    copied_code: "Code snippet copied",
    copied_json: "JSON payload copied",
    error_copy: "Copy failed",
    live_connection: "Live Connection",
    back_to_list: "Back to List",
    sgk_prim_baslik: "SGK Premium and Incentive Info",
    sgk_isci_payi: "Employee Contribution",
    sgk_sabit: "Fixed",
    sgk_isci_aciklama: "SSI + Unemployment Insurance",
    sgk_isveren_tevkisiz: "Employer Contribution (Without Incentive)",
    sgk_standart_oran: "Standard rate",
    sgk_isveren_tevkisli: "Employer Contribution (With Incentive)",
    sgk_indirimli: "Reduced",
    sgk_tesvik_imalat: "5510 — Five-Point Premium Reduction (Manufacturing)",
    sgk_tesvik_diger: "5510 — Two-Point Premium Reduction (Non-Manufacturing)",

    // Catalog & General
    catalog_title: "Data Catalog", catalog_search: "Search dataset...", catalog_loading: "Loading catalog...",
    empty_title: "Select a Dataset or Service", empty_desc: "Choose a dataset from the catalog tree on the left to inspect its parametric API endpoints, data tables and ready-to-use code samples.",
    empty_card1_t: "Data Preview", empty_card1_d: "Live data records in a table view.", empty_card2_t: "Ready-to-use Code", empty_card2_d: "cURL, Python, JS, Go & PHP integrations.",
    bc_home: "Catalog", run_query: "Refresh", endpoint_label: "API Endpoint", copy: "Copy", copy_payload: "Copy Payload",
    tab_table: "Data Table", tab_code: "Code Samples", tab_json: "JSON Console", tab_docs: "Schema Docs",
    table_filter: "Filter table...", page_label: "records", page_of: "/", prev_page: "Previous page", next_page: "Next page",
    docs_title: "Fields and Data Types", docs_field: "Field", docs_type: "Data Type", docs_example: "Example", docs_desc: "Description",
    records: "Records", services: "Datasets", loading_data: "Loading data...", load_error: "Could not fetch data. Endpoint did not respond.",
    filtered: "filtered", filtered_none: "No records match the filter", no_records: "No records found", no_matches: "No dataset found.",
    notlar_title: "Information Notes",
    layer_ham: "Raw", layer_konsolide: "Consolidated", layer_kurallar: "Rule",

    // Product Card
    sayfa_baslik: "Product & Service Card",
    sayfa_aciklama: "Card is generated by source type: GTİP (Product), CPC (Service), NACE (Business), ISCO (Occupation).",
    arama_yer: "Search product/service name, code or GTİP/CPC/NACE/ISCO…",
    filtre_hepsi: "All", kategoriler_title: "Categories", kategoriler_desc: "Filter by source type",
    kategori_hepsi_desc: "All sources", kategori_gtip_desc: "Products (VAT + SCT)", kategori_cpc_desc: "Services (VAT)", kategori_nace_desc: "Business classes", kategori_isco_desc: "Occupation classes",
    bos_baslik: "Start searching", bos_aciklama: "Type in the search box above; results appear in the list.",
    yukleniyor: "Loading data sources…", yuklendi: "Data ready", yukleme_hatasi: "Could not load data sources",
    sonuc_yok_b: "No results found", sonuc_yok_p: "Try a different keyword or code.",
    satir: "rows", agac_gorunumu: "tree view", baglam_not: "Faded rows are context · Highlighted rows are matches",
    kod_baslik: "Codes", kapat: "Close",
    kart_urun: "Product Card", kart_hizmet: "CPC Card", kart_faaliyet: "Business Card", kart_meslek: "Occupation Card",
    kart_urun_desc: "Physical good — subject to VAT and SCT", kart_hizmet_desc: "CPC Classification (Goods or Services)", kart_faaliyet_desc: "Sector/activity code — tax-exempt", kart_meslek_desc: "Occupational classification — tax-exempt",
    alan_adi: "Standard Field Name", deger: "Value / Standard", kurum: "Responsible Agency", vergi: "Tax Information",
    kdv_orani: "VAT Rate", otv_orani: "SCT Rate", kdv_yok: "Not subject to VAT", otv_yok: "Not subject to SCT", otv_muaf: "Exempt", muaf: "Exempt",
    kdv_listesi: "List", kdv_genel: "General Rate", kdv_tevkifat_oran: "VAT Withholding Rate", kdv_tevkifat: "VAT Withholding", uygulanmaz: "Not Applicable",
    tevkifat_uyari: "Should be confirmed based on buyer-seller relationship", tevkifat_satici_beyan: "Full VAT is declared by the seller",
    hizmet_otv_aciklama: "Services are subject to VAT only",
    gtip_kod: "GTİP Code", cpc_kod: "CPC Code", nace_kod: "NACE Code", isco_kod: "ISCO Code",
    urun_ad_tr: "Product Name (TR)", urun_ad_en: "Product Name (EN)", hizmet_ad_tr: "Service Name (TR)", hizmet_ad_en: "Service Name (EN)",
    faaliyet_ad_tr: "Activity Name (TR)", faaliyet_ad_en: "Activity Name (EN)", meslek_ad_tr: "Occupation Name (TR)", meslek_ad_en: "Occupation Name (EN)",
    olcu_birimi: "Unit of Measure", seviye: "Hierarchy Level", seviye_adi: "Level Name", ust_kod: "Parent Code",
    zorunlu_standart: "Mandatory Standard Code", tolerans: "Tolerance / Deviation Limit (%)", tehlike_sinifi: "Hazard Class", zorunlu_sigorta: "Mandatory Insurance",
    gorev_tanimi: "Task Description", beceri_seviyesi: "Skill Level",
    belge_baslik: "Mandatory Documents and Permits", belge_yok: "No documents defined for this record", belge_zorunlu: "MANDATORY", belge_kosullu: "CONDITIONAL", belge_opsiyonel: "OPTIONAL",
    randiman_baslik: "Shrinkage and Yield Rates", randiman_oran: "Yield", fire_oran: "Shrinkage", verimlilik_baslik: "Service Productivity Indicators", hedef_deger: "Target",
    vergi_disi_aciklama: "Sector/occupation code — not subject to VAT/SCT",
    filtre_notu_urun: "Product records (GTİP): VAT and SCT are shown.", filtre_notu_hizmet: "Service records (CPC): VAT is shown; SCT does not apply.",
    filtre_notu_nace: "NACE sector codes: no tax info.", filtre_notu_isco: "ISCO occupation codes: no tax info.",
    kurum_tuik: "TURKSTAT", kurum_ticaret: "Ministry of Trade", kurum_gib: "Revenue Administration", kurum_tse: "Turkish Standards Institution", kurum_calisma: "Ministry of Labour", kurum_tobb: "TOBB", kurum_seddk: "SEDDK", kurum_isg: "OHS Administration",
    islem_tipleri: "Transaction Type", alici_tipleri: "Buyer Type", satici_tipleri: "Seller Type", istisna: "Exemption Status", istisna_var: "Exempt", istisna_yok: "No Exemption", ek_kriterler: "Additional Criteria",
    islem_yurtici: "Domestic Sale", islem_ihracat: "Export", islem_ithalat: "Import",
    tip_kamu: "Public Institution", tip_sirket: "Private Sector (Company)", tip_sahis: "End Consumer / Individual", tip_hepsi: "All Buyers"
  }
};

// --- ORTAK SÖZLÜKLER VE YARDIMCILAR ---

export const TIP_SOZLUK = {
  tr: { liste: 'Liste', agac: 'Ağaç', harita: 'Harita', tablo: 'Tablo', 'kural-seti': 'Kural Seti' },
  en: { liste: 'List', agac: 'Tree', harita: 'Map', tablo: 'Table', 'kural-seti': 'Rule Set' }
};

export const KOD_SISTEMI_MAP = {
  'gtip': { ad: { tr: 'GTİP Kodları', en: 'GTİP Codes' }, ikon: '🚢' }, 'cpc': { ad: { tr: 'CPC Kodları', en: 'CPC Codes' }, ikon: '📊' },
  'nace': { ad: { tr: 'NACE Kodları', en: 'NACE Codes' }, ikon: '🏭' }, 'isco': { ad: { tr: 'ISCO Kodları', en: 'ISCO Codes' }, ikon: '🤝' },
  'sgk': { ad: { tr: 'SGK Verileri', en: 'SGK Data' }, ikon: '🩺' }, 'csgb': { ad: { tr: 'ÇSGB Verileri', en: 'MoLSS Data' }, ikon: '💼' },
  'gib': { ad: { tr: 'GİB Vergi Tarifeleri', en: 'RA Tax Tariffs' }, ikon: '🧾' }, 'hvmb': { ad: { tr: 'HMB Verileri', en: 'MoF Data' }, ikon: '💰' },
  'tuik': { ad: { tr: 'TÜİK Verileri', en: 'TurkStat Data' }, ikon: '📈' }, 'diger': { ad: { tr: 'Diğer Veriler', en: 'Other Data' }, ikon: '🏛️' }
};

export const ALAN_ETIKET_TR = {
  kod: 'Kod', ust_kod: 'Üst Kod', seviye: 'Seviye', seviye_adi: 'Seviye Adı',
  sira: 'Sıra', yaprak: 'Yaprak', ad_tr: 'Ad (TR)', ad_en: 'Ad (EN)',
  tanim_tr: 'Tanım (TR)', tanim_en: 'Tanım (EN)',
  baslik_tr: 'Başlık (TR)', baslik_en: 'Başlık (EN)',
  aciklama_tr: 'Açıklama (TR)', aciklama_en: 'Açıklama (EN)',
  oran: 'Oran', olcu_birimi: 'Ölçü Birimi', para_birimi: 'Para Birimi',
  periyot: 'Periyot', deger: 'Değer', kdv_orani: 'KDV Oranı',
  kdv: 'KDV Bilgisi', otv: 'ÖTV Bilgisi', tevkifat: 'Tevkifat Bilgisi',
  randiman: 'Randıman Bilgisi', kayit_sayisi: 'Kayıt Sayısı',
  dosya: 'Dosya Yolu', bolum_kod: 'Bölüm Kodu', yil: 'Yıl', tutar: 'Tutar',
  derece: 'Derece', dereceler: 'Dereceler', engellilik_orani_min: 'Min. Engellilik Oranı',
  kategoriler: 'Kategoriler', motor_silindir_hacmi: 'Motor Hacmi',
  tasit_degeri_dilimleri: 'Değer Dilimleri', yasi_gruplari: 'Yaş Grupları',
  esik_alt: 'Eşik (Alt)', esik_ust: 'Eşik (Üst)', yapilan: 'Durum',
  arac_turu: 'Araç Türü', not: 'Not', kapsam_tr: 'Kapsam (TR)', kapsam_en: 'Kapsam (EN)'
};

export const ALAN_ETIKET_EN = {
  kod: 'Code', ust_kod: 'Parent Code', seviye: 'Level', seviye_adi: 'Level Name',
  sira: 'Order', yaprak: 'Leaf', ad_tr: 'Name (TR)', ad_en: 'Name (EN)',
  tanim_tr: 'Description (TR)', tanim_en: 'Description (EN)',
  baslik_tr: 'Title (TR)', baslik_en: 'Title (EN)',
  aciklama_tr: 'Explanation (TR)', aciklama_en: 'Explanation (EN)',
  oran: 'Rate', olcu_birimi: 'Unit', para_birimi: 'Currency',
  periyot: 'Period', deger: 'Value', kdv_orani: 'VAT Rate',
  kdv: 'VAT', otv: 'SCT', tevkifat: 'Withholding',
  randiman: 'Yield', kayit_sayisi: 'Record Count',
  dosya: 'File Path', bolum_kod: 'Section Code', yil: 'Year', tutar: 'Amount',
  derece: 'Degree', dereceler: 'Degrees', engellilik_orani_min: 'Min. Disability Rate',
  kategoriler: 'Categories', motor_silindir_hacmi: 'Engine Volume',
  tasit_degeri_dilimleri: 'Value Brackets', yasi_gruplari: 'Age Groups',
  esik_alt: 'Threshold (Low)', esik_ust: 'Threshold (High)', yapilan: 'Status',
  arac_turu: 'Vehicle Type', not: 'Note', kapsam_tr: 'Scope (TR)', kapsam_en: 'Scope (EN)'
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

// Ortak Etiketleme Fonksiyonları
export function tipEtiket(tip) {
  if (!tip) return '—';
  const anahtar = String(tip).toLowerCase();
  return (TIP_SOZLUK[DIL][anahtar]) || tip;
}
export function alanEtiket(anahtar) {
  const sozluk = DIL === 'tr' ? ALAN_ETIKET_TR : ALAN_ETIKET_EN;
  return sozluk[anahtar] || anahtar.replace(/_/g, ' ').replace(/\b\w/g, h => h.toLocaleUpperCase(DIL === 'tr' ? 'tr-TR' : 'en-US'));
}
export function grupEtiket(anahtar) {
  const g = KOD_SISTEMI_MAP[anahtar] || KOD_SISTEMI_MAP['diger'];
  return g.ad[DIL];
}

export function dilUygula() {
  document.documentElement.lang = DIL;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  const trBtn = $('lang-tr'), enBtn = $('lang-en');
  if (trBtn && enBtn) {
    trBtn.className = DIL === 'tr' ? 'px-2 lg:px-2.5 py-1 rounded bg-win-500 text-white transition' : 'px-2 lg:px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
    enBtn.className = DIL === 'en' ? 'px-2 lg:px-2.5 py-1 rounded bg-win-500 text-white transition' : 'px-2 lg:px-2.5 py-1 rounded text-slate-400 hover:text-white transition';
  }
  try { localStorage.setItem(CONFIG.LANG_STORAGE_KEY, DIL); } catch (e) { }
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
  } catch (e) { }
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