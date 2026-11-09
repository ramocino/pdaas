import { $ } from './pdaas-utils.js';
import { CONFIG } from './pdaas-config.js';

export const UI = {
  tr: {
    // --- HEADER / NAV ---
    portal_alt: "Parametrik Veri Servisi (Demo) Portalı",
    nav_portal: "Portal",
    nav_urunhizmetara: "Ürün & Hizmet Ara",
    nav_urunhizmetkarti: "Ürün & Hizmet Kartı",
    nav_muhtasar: "Muhtasar",
    nav_konsolide: "Konsolide",
    nav_personel: "Personel",
    menu: "Menü", katalog_ac: "Veri kataloğunu aç", katalog_kisa: "Veri kataloğu",
    system_active: "Sistem Aktif",

    // --- TOAST / KOPYALAMA ---
    copied: "Kopyalandı",
    copied_url: "Endpoint adresi kopyalandı",
    copied_code: "Hazır kod kopyalandı",
    copied_json: "JSON payload kopyalandı",
    error_copy: "Kopyalanamadı",
    live_connection: "Canlı Bağlantı",
    back_to_list: "Listeye Dön",

    // --- SGK ---
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

    // --- KATALOG / BOŞ DURUM ---
    catalog_title: "Veri Kataloğu", catalog_search: "Veri seti ara...", catalog_loading: "Katalog yükleniyor...",
    empty_title: "Veri Seti veya Servis Seçin",
    empty_desc: "Sol taraftaki katalog ağacından bir veri seti seçerek, altındaki parametrik API servis uç noktalarını, veri tablolarını ve hazır kod örneklerini inceleyebilirsiniz. ⚠️ Bu portal makale için demo bir ortamdır. Resmi veri sayfası değildir.",
    empty_card1_t: "Veri Önizleme", empty_card1_d: "Tablo görünümü ile doğrudan canlı veri kayıtları.",
    empty_card2_t: "Hazır Kodlar", empty_card2_d: "cURL, Python, JS, Go & PHP entegrasyonu.",

    // --- SERVİS DETAY ---
    bc_home: "Katalog", run_query: "Yenile", endpoint_label: "API Uç Noktası",
    copy: "Kopyala", copy_payload: "Payload'ı Kopyala",
    tab_table: "Veri Tablosu", tab_code: "Bağlantı Kodları", tab_json: "JSON Konsolu", tab_docs: "Şema Dokümantasyonu",
    table_filter: "Tabloda filtrele...", page_label: "kayıt", page_of: "/", prev_page: "Önceki sayfa", next_page: "Sonraki sayfa",
    docs_title: "Veri Alanları ve Veri Tipleri", docs_field: "Alan Adı", docs_type: "Veri Tipi", docs_example: "Örnek", docs_desc: "Açıklama",
    records: "Kayıt", services: "Veri Seti", loading_data: "Veriler yükleniyor...", load_error: "Veri alınamadı. Endpoint yanıt vermedi.",
    filtered: "filtrelendi", filtered_none: "Filtreye uygun kayıt bulunamadı", no_records: "Kayıt bulunamadı", no_matches: "Eşleşen veri seti bulunamadı.",
    notlar_title: "Bilgi Notları",
    layer_ham: "Ham", layer_konsolide: "Konsolide", layer_kurallar: "Kural", layer_ornek: "Örnek",
    bool_true: "Evet", bool_false: "Hayır", item_count: "öğe", field_count: "alan", section_label: "Bölüm",
    json_scroll: "devamı için aşağı kaydırın", catalog_invalid: "Katalogda servisler listesi bulunamadı.",
    endpoint_missing: "JSON adresi bulunamadı.", json_error: "HATA", total_label: "Toplam", related_records: "kayıt",
    section_urun_kurallari: "Ürün kuralları", section_faaliyet_kurallari: "Faaliyet kuralları",
    section_meslek_kurallari: "Meslek kuralları", section_isco_nace_kurallari: "ISCO–NACE kuralları",
    section_kayitlar: "Kayıtlar", section_kurallar: "Kurallar", section_istisnalar: "İstisnalar",
    section_ithalat: "İthalat", section_ihracat: "İhracat",

    // --- ÜRÜN & HİZMET KARTI ---
    sayfa_baslik: "Ürün & Hizmet Kartı",
    sayfa_aciklama: "Kaynak türüne göre kart üretilir: GTİP (Ürün), CPC (Hizmet), NACE (Faaliyet), ISCO (Meslek).",
    arama_yer: "Ürün/hizmet adı, kod veya GTİP/CPC/NACE/ISCO ara…",
    filtre_hepsi: "Tümü", kategoriler_title: "Kategoriler", kategoriler_desc: "Kaynak türüne göre filtreleyin",
    kategori_hepsi_desc: "Tüm kaynaklar", kategori_gtip_desc: "Ürünler (KDV + ÖTV)", kategori_cpc_desc: "Hizmetler (KDV)",
    kategori_nace_desc: "Faaliyet sınıfları", kategori_isco_desc: "Meslek sınıfları",
    bos_baslik: "Aramaya başlayın", bos_aciklama: "Yukarıdaki arama kutusuna yazın; sonuçlar listede görünür. Bir kayda tıkladığınızda detay kartı açılır.",
    yukleniyor: "Veriler yükleniyor…", yuklendi: "Veriler hazır", yukleme_hatasi: "Veri kaynakları yüklenemedi",
    sonuc_yok_b: "Sonuç bulunamadı", sonuc_yok_p: "Farklı bir kelime veya kod deneyin.",
    satir: "satır", agac_gorunumu: "ağaç görünümü", baglam_not: "Soluk satırlar bağlam · Koyu satırlar arama eşleşmesi",
    kod_baslik: "Kodları", kapat: "Kapat",
    kart_urun: "Ürün Kartı", kart_hizmet: "CPC Kartı", kart_faaliyet: "Faaliyet Kartı", kart_meslek: "Meslek Kartı",
    kart_urun_desc: "Fiziki mal — KDV ve ÖTV'ye tabidir",
    kart_hizmet_desc: "CPC Sınıflandırması (Ürün veya Hizmet)",
    kart_faaliyet_desc: "Sektör/faaliyet kodu — vergi dışıdır",
    kart_meslek_desc: "Meslek sınıflaması — vergi dışıdır",
    alan_adi: "Standart Alan Adı", deger: "Değer / Standart", kurum: "Sorumlu Kurum", vergi: "Vergi Bilgileri",
    kdv_orani: "KDV Oranı", otv_orani: "ÖTV Oranı",
    kdv_yok: "Bu kayıt KDV'ye tabi değildir", otv_yok: "Bu kayıt ÖTV'ye tabi değildir",
    otv_muaf: "Muaf", muaf: "Muaf",
    kdv_listesi: "Liste", kdv_genel: "Genel Oran", kdv_tevkifat_oran: "KDV Tevkifat Oranı",
    kdv_tevkifat: "KDV Tevkifatı", uygulanmaz: "Uygulanmaz",
    tevkifat_uyari: "Alıcı-satıcı ilişkisine göre teyit edilmeli",
    tevkifat_satici_beyan: "KDV'nin tamamı satıcı tarafından beyan edilir",
    hizmet_otv_aciklama: "Hizmetler yalnızca KDV'ye tabidir",
    gtip_kod: "GTİP Kodu", cpc_kod: "CPC Kodu", nace_kod: "NACE Kodu", isco_kod: "ISCO Kodu",
    urun_ad_tr: "Ürün Adı (TR)", urun_ad_en: "Ürün Adı (EN)",
    hizmet_ad_tr: "Hizmet Adı (TR)", hizmet_ad_en: "Hizmet Adı (EN)",
    faaliyet_ad_tr: "Faaliyet Adı (TR)", faaliyet_ad_en: "Faaliyet Adı (EN)",
    meslek_ad_tr: "Meslek Adı (TR)", meslek_ad_en: "Meslek Adı (EN)",
    olcu_birimi: "Ölçü Birimi", seviye: "Hiyerarşi Seviyesi", seviye_adi: "Seviye Adı", ust_kod: "Üst Kod",
    zorunlu_standart: "Zorunlu Standart Kodu", tolerans: "Tolerans / Sapma Limiti (%)",
    tehlike_sinifi: "Tehlike Sınıfı", zorunlu_sigorta: "Zorunlu Sigorta",
    gorev_tanimi: "Görev Tanımı", beceri_seviyesi: "Beceri Seviyesi",
    belge_baslik: "Zorunlu Belgeler ve İzinler", belge_yok: "Bu kayıt için tanımlanmış belge bulunamadı",
    belge_zorunlu: "ZORUNLU", belge_kosullu: "KOŞULLU", belge_opsiyonel: "OPSİYONEL",
    randiman_baslik: "Fire ve Randıman Oranları", randiman_oran: "Randıman", fire_oran: "Fire",
    verimlilik_baslik: "Hizmet Verimlilik Göstergeleri", hedef_deger: "Hedef",
    vergi_disi_aciklama: "Sektör/meslek kodu — KDV/ÖTV konusu değildir",
    filtre_notu_urun: "Ürün kayıtları (GTİP): KDV ve ÖTV gösterilir.",
    filtre_notu_hizmet: "Hizmet kayıtları (CPC): KDV gösterilir; ÖTV uygulanmaz.",
    filtre_notu_nace: "NACE sektör kodları: vergi bilgisi yoktur.",
    filtre_notu_isco: "ISCO meslek kodları: vergi bilgisi yoktur.",
    kurum_tuik: "TÜİK", kurum_ticaret: "Ticaret Bakanlığı", kurum_gib: "GİB", kurum_tse: "TSE",
    kurum_calisma: "Çalışma Bakanlığı", kurum_tobb: "TOBB", kurum_seddk: "SEDDK", kurum_isg: "İSGGM",
    islem_tipleri: "İşlem Tipi", alici_tipleri: "Alıcı Tipi", satici_tipleri: "Satıcı Tipi",
    istisna: "İstisna Durumu", istisna_var: "İstisna Uygulanır", istisna_yok: "İstisna Yok",
    ek_kriterler: "Ek Kriterler",
    islem_yurtici: "Yurtiçi Satış", islem_ihracat: "İhracat (Yurtdışı)", islem_ithalat: "İthalat",
    tip_kamu: "Kamu Kurumu", tip_sirket: "Özel Sektör (Şirket)", tip_sahis: "Nihai Tüketici / Şahıs", tip_hepsi: "Tüm Alıcılar",

    // --- ÜRÜN KARTI EK (urunhizmetkarti.html) ---
    bagli_cpc: "CPC eşleşmesi", bagli_nace: "NACE eşleşmesi", bagli_gtip: "GTİP eşleşmesi", bagli_isco: "ISCO eşleşmesi",
    bagli_tesvik: "Teşvik adayı", bagli_sgk: "SGK meslek adayı", bagli_mesleki: "Mesleki belge",
    bagli_vergi: "Vergi bilgisi", bagli_randiman: "Randıman bilgisi", bagli_belge: "Belge bilgisi",
    iliskili_kodlar: "İlişkili sınıflandırma kodları", iliskili: "İlişkili",
    tumunu_goster: "Tümünü göster", daha_az: "Daha az göster",
    kod: "Kod", iliskili_kod_sayisi: "İlişkili {tur} kodları",
    urun_adi: "Ürün adı", hizmet_adi: "Ürün / hizmet adı",
    faaliyet_adi: "Faaliyet adı", meslek_adi: "Meslek adı",
    kod_bulunamadi: "İlgili kod veri setinde bulunamadı.", kaynak_yuklenemedi: "Veri seti henüz yüklenmedi.",
    bilgi: "Bilgi", hata: "Hata", genel_belgeler: "Genel belgeler",
    mesleki_belgeler: "Mesleki belgeler ve yeterlilikler", belge_adi: "Belge adı",
    tur: "Tür", durum: "Durum", aciklama: "Açıklama", puan: "Puan",
    tesvik_adaylari: "Teşvik adayları (SGK)", sgk_aday: "SGK meslek adayları",
    ulke_turkiye: "Türkiye", dis_alim: "Dış alım", yurt_disi: "Yurt dışı",
    gumruk_vergisi: "Gümrük vergisi", mense: "Menşe", bilinmiyor: "Bilinmiyor",
    gtip_bazli: "GTİP koduna göre değişir", gtip_ayrinti: "İlgili GTİP kartlarından inceleyin",
    tarife_yok: "Genel tarife bilgisi bulunamadı", oran_bilinmiyor: "Oran belirtilmemiş",
    tur_diploma: "Diploma", tur_ruhsat: "Ruhsat", tur_tescil: "Tescil", tur_yeterlilik: "Yeterlilik",
    mense_diger_ulkeler: "Diğer ülkeler", yukari_git: "Yukarı git",

    // --- MUHTASAR (muhtasar.html) ---
    muh_baslik: "Muhtasar Beyanname Tablosu",
    muh_aciklama: "Personel verilerini girin veya seçin. Tüm oranlar ve kodlar API üzerinden çekilir.",
    muh_ref_baslik: "Referans Veriler",
    muh_kaynak_baslik: "Veri Kaynakları (API)",
    muh_tablo_baslik: "Beyanname Detayları (2026 / 10)",
    muh_th_belge: "Belge Türü", muh_th_tc: "TC Kimlik No", muh_th_ad: "Adı", muh_th_soyad: "Soyadı",
    muh_th_gun: "Gün", muh_th_ucret: "Ücret (Brüt)", muh_th_cikis: "İşten Çıkış Nedeni",
    muh_th_eksik: "Eksik Gün Nedeni", muh_th_meslek: "Meslek Kodu",
    muh_th_brut10: "Brüt Ücret (10 Aylık)", muh_th_gv_matrah: "Gelir Vergisi Matrahı (Bu Ay)",
    muh_th_gv: "Gelir Vergisi Kesintisi", muh_th_dv: "Damga Vergisi Kesintisi", muh_toplam: "TOPLAM",
    muh_yukleniyor: "Referans veriler yükleniyor…", muh_hazir: "Referans veriler hazır", muh_sec: "Seçiniz",
    muh_kaynak_ok: "yüklendi", muh_kaynak_hata: "yüklenemedi",
    muh_placeholder_tc: "11 Haneli TC", muh_placeholder_ad: "Adı", muh_placeholder_soyad: "Soyadı",
    muh_asgari_aylik_brut: "Aylık Brüt Asgari Ücret", muh_asgari_aylik_net: "Aylık Net Asgari Ücret",
    muh_asgari_gunluk_brut: "Günlük Brüt Asgari Ücret", muh_asgari_gunluk_net: "Günlük Net Asgari Ücret",
    muh_damga: "Damga Vergisi", muh_sgk_isci: "İşçi SGK Payı", muh_issizlik_isci: "İşçi İşsizlik Payı",
    muh_kaynak_yedek: "Örnek değer", muh_kaynak_dogrulandi: "JSON kaynağı",
    muh_veri_eksik: "Bazı referans dosyaları okunamadı; örnek değerler kullanılıyor. Bu sonuçları resmî hesaplama olarak kullanmayın.",
    muh_eksik_kaynaklar: "Kontrol edilmesi gereken kaynaklar", muh_kaynak_icerigi: "Gerekli kayıtlar bulunamadı",
    muh_baglanti_hatasi: "Bağlantı hatası", muh_json_gecersiz: "JSON okunamadı",
    muh_veri_yok: "Veri yok", muh_uyari_baslik: "Örnek hesaplama"
  },
  en: {
    // --- HEADER / NAV ---
    portal_alt: "Parametric Data Service (Demo) Portal",
    nav_portal: "Portal",
    nav_urunhizmetara: "Products & Services Search",
    nav_urunhizmetkarti: "Products & Services Card",
    nav_muhtasar: "Withholding",
    nav_konsolide: "Konsolide",
    nav_personel: "Personnel",
    menu: "Menu", katalog_ac: "Open data catalog", katalog_kisa: "Data catalog",
    system_active: "System Active",

    // --- TOAST / COPY ---
    copied: "Copied",
    copied_url: "Endpoint URL copied",
    copied_code: "Code snippet copied",
    copied_json: "JSON payload copied",
    error_copy: "Copy failed",
    live_connection: "Live Connection",
    back_to_list: "Back to List",

    // --- SGK ---
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

    // --- CATALOG / EMPTY ---
    catalog_title: "Data Catalog", catalog_search: "Search dataset...", catalog_loading: "Loading catalog...",
    empty_title: "Select a Dataset or Service",
    empty_desc: "⚠️Choose a dataset from the catalog tree on the left to inspect its parametric API endpoints, data tables and ready-to-use code samples. ⚠️ This portal is a demo environment for an article. It is not an official data page.",
    empty_card1_t: "Data Preview", empty_card1_d: "Live data records in a table view.",
    empty_card2_t: "Ready-to-use Code", empty_card2_d: "cURL, Python, JS, Go & PHP integrations.",

    // --- SERVICE DETAIL ---
    bc_home: "Catalog", run_query: "Refresh", endpoint_label: "API Endpoint",
    copy: "Copy", copy_payload: "Copy Payload",
    tab_table: "Data Table", tab_code: "Code Samples", tab_json: "JSON Console", tab_docs: "Schema Docs",
    table_filter: "Filter table...", page_label: "records", page_of: "/", prev_page: "Previous page", next_page: "Next page",
    docs_title: "Fields and Data Types", docs_field: "Field", docs_type: "Data Type", docs_example: "Example", docs_desc: "Description",
    records: "Records", services: "Datasets", loading_data: "Loading data...", load_error: "Could not fetch data. Endpoint did not respond.",
    filtered: "filtered", filtered_none: "No records match the filter", no_records: "No records found", no_matches: "No dataset found.",
    notlar_title: "Information Notes",
    layer_ham: "Raw", layer_konsolide: "Consolidated", layer_kurallar: "Rule", layer_ornek: "Example",
    bool_true: "Yes", bool_false: "No", item_count: "items", field_count: "fields", section_label: "Section",
    json_scroll: "scroll down to load more", catalog_invalid: "The catalog does not contain a services list.",
    endpoint_missing: "No JSON endpoint was found.", json_error: "ERROR", total_label: "Total", related_records: "records",
    section_urun_kurallari: "Product rules", section_faaliyet_kurallari: "Activity rules",
    section_meslek_kurallari: "Occupation rules", section_isco_nace_kurallari: "ISCO–NACE rules",
    section_kayitlar: "Records", section_kurallar: "Rules", section_istisnalar: "Exemptions",
    section_ithalat: "Import", section_ihracat: "Export",

    // --- PRODUCT & SERVICE CARD ---
    sayfa_baslik: "Product & Service Card",
    sayfa_aciklama: "Card is generated by source type: GTİP (Product), CPC (Service), NACE (Business), ISCO (Occupation).",
    arama_yer: "Search product/service name, code or GTİP/CPC/NACE/ISCO…",
    filtre_hepsi: "All", kategoriler_title: "Categories", kategoriler_desc: "Filter by source type",
    kategori_hepsi_desc: "All sources", kategori_gtip_desc: "Products (VAT + SCT)", kategori_cpc_desc: "Services (VAT)",
    kategori_nace_desc: "Business classes", kategori_isco_desc: "Occupation classes",
    bos_baslik: "Start searching", bos_aciklama: "Type in the search box above; results appear in the list.",
    yukleniyor: "Loading data sources…", yuklendi: "Data ready", yukleme_hatasi: "Could not load data sources",
    sonuc_yok_b: "No results found", sonuc_yok_p: "Try a different keyword or code.",
    satir: "rows", agac_gorunumu: "tree view", baglam_not: "Faded rows are context · Highlighted rows are matches",
    kod_baslik: "Codes", kapat: "Close",
    kart_urun: "Product Card", kart_hizmet: "CPC Card", kart_faaliyet: "Business Card", kart_meslek: "Occupation Card",
    kart_urun_desc: "Physical good — subject to VAT and SCT",
    kart_hizmet_desc: "CPC Classification (Goods or Services)",
    kart_faaliyet_desc: "Sector/activity code — tax-exempt",
    kart_meslek_desc: "Occupational classification — tax-exempt",
    alan_adi: "Standard Field Name", deger: "Value / Standard", kurum: "Responsible Agency", vergi: "Tax Information",
    kdv_orani: "VAT Rate", otv_orani: "SCT Rate",
    kdv_yok: "Not subject to VAT", otv_yok: "Not subject to SCT",
    otv_muaf: "Exempt", muaf: "Exempt",
    kdv_listesi: "List", kdv_genel: "General Rate", kdv_tevkifat_oran: "VAT Withholding Rate",
    kdv_tevkifat: "VAT Withholding", uygulanmaz: "Not Applicable",
    tevkifat_uyari: "Should be confirmed based on buyer-seller relationship",
    tevkifat_satici_beyan: "Full VAT is declared by the seller",
    hizmet_otv_aciklama: "Services are subject to VAT only",
    gtip_kod: "GTİP Code", cpc_kod: "CPC Code", nace_kod: "NACE Code", isco_kod: "ISCO Code",
    urun_ad_tr: "Product Name (TR)", urun_ad_en: "Product Name (EN)",
    hizmet_ad_tr: "Service Name (TR)", hizmet_ad_en: "Service Name (EN)",
    faaliyet_ad_tr: "Activity Name (TR)", faaliyet_ad_en: "Activity Name (EN)",
    meslek_ad_tr: "Occupation Name (TR)", meslek_ad_en: "Occupation Name (EN)",
    olcu_birimi: "Unit of Measure", seviye: "Hierarchy Level", seviye_adi: "Level Name", ust_kod: "Parent Code",
    zorunlu_standart: "Mandatory Standard Code", tolerans: "Tolerance / Deviation Limit (%)",
    tehlike_sinifi: "Hazard Class", zorunlu_sigorta: "Mandatory Insurance",
    gorev_tanimi: "Task Description", beceri_seviyesi: "Skill Level",
    belge_baslik: "Mandatory Documents and Permits", belge_yok: "No documents defined for this record",
    belge_zorunlu: "MANDATORY", belge_kosullu: "CONDITIONAL", belge_opsiyonel: "OPTIONAL",
    randiman_baslik: "Shrinkage and Yield Rates", randiman_oran: "Yield", fire_oran: "Shrinkage",
    verimlilik_baslik: "Service Productivity Indicators", hedef_deger: "Target",
    vergi_disi_aciklama: "Sector/occupation code — not subject to VAT/SCT",
    filtre_notu_urun: "Product records (GTİP): VAT and SCT are shown.",
    filtre_notu_hizmet: "Service records (CPC): VAT is shown; SCT does not apply.",
    filtre_notu_nace: "NACE sector codes: no tax info.",
    filtre_notu_isco: "ISCO occupation codes: no tax info.",
    kurum_tuik: "TURKSTAT", kurum_ticaret: "Ministry of Trade", kurum_gib: "Revenue Administration",
    kurum_tse: "Turkish Standards Institution", kurum_calisma: "Ministry of Labour", kurum_tobb: "TOBB",
    kurum_seddk: "SEDDK", kurum_isg: "OHS Administration",
    islem_tipleri: "Transaction Type", alici_tipleri: "Buyer Type", satici_tipleri: "Seller Type",
    istisna: "Exemption Status", istisna_var: "Exempt", istisna_yok: "No Exemption",
    ek_kriterler: "Additional Criteria",
    islem_yurtici: "Domestic Sale", islem_ihracat: "Export", islem_ithalat: "Import",
    tip_kamu: "Public Institution", tip_sirket: "Private Sector (Company)", tip_sahis: "End Consumer / Individual", tip_hepsi: "All Buyers",

    // --- PRODUCT CARD EXTRA (urunhizmetkarti.html) ---
    bagli_cpc: "CPC mapping", bagli_nace: "NACE mapping", bagli_gtip: "GTİP mapping", bagli_isco: "ISCO mapping",
    bagli_tesvik: "Incentive candidate", bagli_sgk: "Candidate SGK occupations", bagli_mesleki: "Occupational credential",
    bagli_vergi: "Tax information", bagli_randiman: "Yield information", bagli_belge: "Document information",
    iliskili_kodlar: "Related classification codes", iliskili: "Related",
    tumunu_goster: "Show all", daha_az: "Show less",
    kod: "Code", iliskili_kod_sayisi: "Related {tur} codes",
    urun_adi: "Product name", hizmet_adi: "Product / service name",
    faaliyet_adi: "Activity name", meslek_adi: "Occupation name",
    kod_bulunamadi: "The requested code was not found in the dataset.", kaynak_yuklenemedi: "The dataset has not loaded yet.",
    bilgi: "Information", hata: "Error", genel_belgeler: "General documents",
    mesleki_belgeler: "Occupational credentials and qualifications", belge_adi: "Document name",
    tur: "Type", durum: "Status", aciklama: "Description", puan: "Points",
    tesvik_adaylari: "Incentive candidates (SSI)", sgk_aday: "Candidate SGK occupations",
    ulke_turkiye: "Türkiye", dis_alim: "Import", yurt_disi: "Export",
    gumruk_vergisi: "Customs duty", mense: "Origin", bilinmiyor: "Unknown",
    gtip_bazli: "Varies by GTİP code", gtip_ayrinti: "Check the associated GTİP cards",
    tarife_yok: "No general tariff information available", oran_bilinmiyor: "Rate not specified",
    tur_diploma: "Diploma", tur_ruhsat: "Licence", tur_tescil: "Registration", tur_yeterlilik: "Qualification",
    mense_diger_ulkeler: "Other countries", yukari_git: "Back to top",

    // --- WITHHOLDING (muhtasar.html) ---
    muh_baslik: "Withholding Tax Return Table",
    muh_aciklama: "Enter or select employee data. All rates and codes are fetched via API.",
    muh_ref_baslik: "Reference Data",
    muh_kaynak_baslik: "Data Sources (API)",
    muh_tablo_baslik: "Return Details (2026 / 10)",
    muh_th_belge: "Document Type", muh_th_tc: "ID Number", muh_th_ad: "First Name", muh_th_soyad: "Last Name",
    muh_th_gun: "Days", muh_th_ucret: "Wage (Gross)", muh_th_cikis: "Termination Reason",
    muh_th_eksik: "Missing Days Reason", muh_th_meslek: "Occupation Code",
    muh_th_brut10: "Gross Wage (10 Months)", muh_th_gv_matrah: "Income Tax Base (This Month)",
    muh_th_gv: "Income Tax Deduction", muh_th_dv: "Stamp Tax Deduction", muh_toplam: "TOTAL",
    muh_yukleniyor: "Loading reference data…", muh_hazir: "Reference data ready", muh_sec: "Select",
    muh_kaynak_ok: "loaded", muh_kaynak_hata: "failed",
    muh_placeholder_tc: "11 Digit ID", muh_placeholder_ad: "First Name", muh_placeholder_soyad: "Last Name",
    muh_asgari_aylik_brut: "Monthly Gross Min. Wage", muh_asgari_aylik_net: "Monthly Net Min. Wage",
    muh_asgari_gunluk_brut: "Daily Gross Min. Wage", muh_asgari_gunluk_net: "Daily Net Min. Wage",
    muh_damga: "Stamp Tax", muh_sgk_isci: "Employee SGK Share", muh_issizlik_isci: "Employee Unemployment Share",
    muh_kaynak_yedek: "Sample value", muh_kaynak_dogrulandi: "JSON source",
    muh_veri_eksik: "Some reference files could not be loaded; sample values are being used. Do not use these results for official calculations.",
    muh_eksik_kaynaklar: "Sources to check", muh_kaynak_icerigi: "Required records are missing",
    muh_baglanti_hatasi: "Connection error", muh_json_gecersiz: "JSON could not be parsed",
    muh_veri_yok: "Data unavailable", muh_uyari_baslik: "Illustrative calculation"
  }
};

// --- ORTAK SÖZLÜKLER VE YARDIMCILAR (değişmedi) ---

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
  arac_turu: 'Araç Türü', not: 'Not', kapsam_tr: 'Kapsam (TR)', kapsam_en: 'Kapsam (EN)',
  belge_ref: 'Belge Referansı', belge_kodlari: 'Belge Kodları', islem_tipleri: 'İşlem Türleri',
  durum: 'Durum', kosul: 'Koşul', gtip_prefixler: 'GTİP Önekleri', nace_prefixler: 'NACE Önekleri',
  haric_nace_prefixler: 'Hariç NACE Önekleri', isco_kodlari: 'ISCO Kodları',
  urun_kurallari: 'Ürün Kuralları', faaliyet_kurallari: 'Faaliyet Kuralları', meslek_kurallari: 'Meslek Kuralları'
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
  arac_turu: 'Vehicle Type', not: 'Note', kapsam_tr: 'Scope (TR)', kapsam_en: 'Scope (EN)',
  belge_ref: 'Document Reference', belge_kodlari: 'Document Codes', islem_tipleri: 'Transaction Types',
  durum: 'Status', kosul: 'Condition', gtip_prefixler: 'GTİP Prefixes', nace_prefixler: 'NACE Prefixes',
  haric_nace_prefixler: 'Excluded NACE Prefixes', isco_kodlari: 'ISCO Codes',
  urun_kurallari: 'Product Rules', faaliyet_kurallari: 'Activity Rules', meslek_kurallari: 'Occupation Rules'
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
export function kayitAdi(k) { return alanSec(k, 'tanim') || alanSec(k, 'ad') || '—'; }
export function aciklamaAdi(o) { return alanSec(o, 'aciklama'); }

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
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.dataset.i18nTitle); });
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel)); });
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