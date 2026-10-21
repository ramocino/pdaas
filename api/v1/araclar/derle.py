#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def yukle(yol):
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")


def kanonik(veri):
    return json.dumps(veri, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(veri):
    return "sha256:" + hashlib.sha256(kanonik(veri)).hexdigest()


def dosya_bul(kok, dosya_adi):
    """Dosyayı doğrudan kök dizinde arar ve (veri, hash) döndürür."""
    yol = kok / dosya_adi
    if not yol.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {yol}")
    doc = yukle(yol)
    return doc, sha256(doc.get("kayitlar", doc.get("kurallar", doc)))


# ---------------------------------------------------------------------------
# Semantik doğrulama: bilinen eşleştirme hatalarını yakalar
# ---------------------------------------------------------------------------

def sanity_check(kod, tanim_tr, kdv_data, otv_data, uyarilar):
    """Bilinen eşleştirme hatalarını yakalar. Derlemeyi durdurmaz, uyarı toplar."""

    kdv_grp = (kdv_data or {}).get("grup") or ""
    kdv_oran = (kdv_data or {}).get("oran")
    otv_grp = (otv_data or {}).get("grup") or ""

    # 1. Chapter 22 (alkollü içecekler) tütün grubunda olamaz
    if kod.startswith(("2203", "2204", "2205", "2206", "2207", "2208")):
        if otv_grp.startswith("OTV-III-B") or "Tutun" in otv_grp:
            uyarilar.append(
                f"{kod} ({tanim_tr[:45]}): alkollü içecek tütün grubunda -> {otv_grp}"
            )

    # 2. III/A alt grupları doğru mu?
    if kod.startswith("2203") and otv_grp != "OTV-III-A-Bira":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): 2203 bira grubunda değil -> {otv_grp}")
    if kod.startswith(("2204", "2205", "2206")) and otv_grp != "OTV-III-A-Sarap":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): şarap/fermente grubunda değil -> {otv_grp}")
    if kod.startswith(("220720001015", "220720009015")) and otv_grp != "OTV-III-A-EtilAlkol":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): 220720 damıtım alkollü içki grubunda değil -> {otv_grp}")
    if kod.startswith("220210000013"):
        if otv_grp != "OTV-III-A-KolaliGazoz":
            uyarilar.append(f"{kod} ({tanim_tr[:45]}): kolalı gazoz KolaliGazoz grubunda değil -> {otv_grp}")
    elif kod.startswith(("2009", "2202")) and otv_grp != "OTV-III-A-Mesrubat":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): alkolsüz içecek Mesrubat grubunda değil -> {otv_grp}")
    if kod.startswith("2208") and otv_grp != "OTV-III-A-AlkolluIcecek":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): 2208 diğer alkollü içecek grubunda değil -> {otv_grp}")

    # 3. KDV genel oran kontrolü (genel %20 olması gerekenler)
    if kod.startswith(("8703", "340", "481810", "481820", "481830")) and kdv_oran is not None and kdv_oran != 0.20:
        uyarilar.append(
            f"{kod} ({tanim_tr[:45]}): KDV %{kdv_oran*100:.0f} (genel %20 olmalı; grup={kdv_grp})"
        )

    # 4. 2402, 2403 tütün grubunda olmalı
    if kod.startswith(("2402", "2403")) and otv_grp != "OTV-III-B-Tutun":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): tütün grubunda değil -> {otv_grp}")

    # 5. 2404 nikotin/tütün ürünleri tütün grubunda olmalı (2404.92 hariç)
    if (kod.startswith(("240411", "240412", "240419", "240491", "240499"))
            and otv_grp != "OTV-III-B-Tutun"):
        uyarilar.append(
            f"{kod} ({tanim_tr[:45]}): 2404 nikotin/tütün ürünü tütün grubunda değil -> {otv_grp}"
        )

    # 6. 2404.92 transdermal nikotin bandı ÖTV'ye tabi olmamalı
    #    TİTCK tarafından beşeri tıbbi ürün olarak ruhsatlandırılmıştır.
    if kod.startswith("240492") and otv_grp and otv_grp != "otv_yok":
        uyarilar.append(
            f"{kod} ({tanim_tr[:45]}): transdermal nikotin bandı ÖTV'ye tabi olmamalı -> {otv_grp}"
        )

    # 7. 8517 (telefonlar) KDV %1 olamaz (yenilenmiş istisnası işlem bazlı, GTİP bazlı değil)
    if kod.startswith("8517") and kdv_oran is not None and kdv_oran < 0.20:
        uyarilar.append(
            f"{kod} ({tanim_tr[:45]}): KDV %{kdv_oran*100:.0f} (genel %20 olmalı; grup={kdv_grp})"
        )

    # 8. 2710198 / 2710199 (madeni yağ) akaryakıt grubunda olamaz
    if kod.startswith(("2710198", "2710199")) and otv_grp == "OTV-I-A-Akaryakit":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): madeni yağ akaryakıt grubunda")

# ---------------------------------------------------------------------------
# Yazma yardımcıları
# ---------------------------------------------------------------------------

def parcala_ve_yaz(kok, servis_kod, ad_tr, ad_en, kayitlar, meta_kaynak):
    hedef_klasor = kok / servis_kod
    fasil_klasor = hedef_klasor / "fasil"

    gruplar = {}
    for k in kayitlar:
        fasil = str(k.get("kod", "00"))[:2]
        gruplar.setdefault(fasil, []).append(k)

    bugun = datetime.date.today()
    temel_meta = {
        "schema_surumu": "1.0.0",
        "servis": {"kod": servis_kod, "ad": {"tr": ad_tr, "en": ad_en}},
        "katman": "konsolide",
        "yapi": {"tip": "liste", "kod_sistemi": "gtip", "kapsam": ["vergi", "ticaret"]},
        "surum": bugun.strftime("%Y.%m.%d"),
        "guncelleme": bugun.isoformat(),
        "yayin_durumu": "yayinda",
        "zaman": {"bazli": False, "baslangic": None, "bitis": None},
        "yayinci": meta_kaynak["yayinci"],
        "kaynaklar": meta_kaynak.get("kaynaklar", []),
        "mevzuat_ref": meta_kaynak.get("mevzuat_ref", []),
        "uretim": meta_kaynak["uretim"],
    }

    for fasil, f_kayitlar in gruplar.items():
        parca_meta = dict(temel_meta)
        parca_meta["parca"] = {"tur": "fasil", "kod": fasil, "ana_dosya": "index.json"}
        yaz(fasil_klasor / f"{fasil}.json", {"meta": parca_meta, "kayitlar": f_kayitlar})

    index_meta = dict(temel_meta)
    yaz(hedef_klasor / "index.json", {
        "meta": index_meta,
        "fasillar": [
            {"kod": fasil, "kayit_sayisi": len(f_kayitlar), "dosya": f"fasil/{fasil}.json"}
            for fasil, f_kayitlar in sorted(gruplar.items())
        ],
    })
    print(f"  -> {servis_kod} (Klasör): {len(gruplar)} fasıl.")


def tum_veriyi_yaz(kok, servis_kod, ad_tr, ad_en, kayitlar, meta_kaynak):
    bugun = datetime.date.today()
    temel_meta = {
        "schema_surumu": "1.0.0",
        "servis": {"kod": servis_kod, "ad": {"tr": ad_tr, "en": ad_en}},
        "katman": "konsolide",
        "yapi": {"tip": "liste", "kod_sistemi": "gtip", "kapsam": ["vergi", "ticaret"]},
        "surum": bugun.strftime("%Y.%m.%d"),
        "guncelleme": bugun.isoformat(),
        "yayin_durumu": "yayinda",
        "zaman": {"bazli": False, "baslangic": None, "bitis": None},
        "yayinci": meta_kaynak["yayinci"],
        "kaynaklar": meta_kaynak.get("kaynaklar", []),
        "mevzuat_ref": meta_kaynak.get("mevzuat_ref", []),
        "uretim": meta_kaynak["uretim"],
    }
    yaz(kok / f"{servis_kod}.json", {"meta": temel_meta, "kayitlar": kayitlar})
    print(f"  -> {servis_kod}.json (Tek Dosya) oluşturuldu.")


# ---------------------------------------------------------------------------
# Eşleştirme
# ---------------------------------------------------------------------------

def eslesme_yap(kok):
    print("Konsolide derleme başladı...")

    gtip_doc, gtip_hash = dosya_bul(kok, "gtip-kodlari.json")
    kdv_oran_doc, kdv_oran_hash = dosya_bul(kok, "kdv-oranlari.json")
    kdv_kural_doc, kdv_kural_hash = dosya_bul(kok, "kdv-kurallar.json")
    otv_oran_doc, otv_oran_hash = dosya_bul(kok, "otv-oranlari.json")
    otv_kural_doc, otv_kural_hash = dosya_bul(kok, "otv-kurallar.json")
    tevkifat_oran_doc, tevkifat_oran_hash = dosya_bul(kok, "tevkifat-oranlari.json")
    tevkifat_kural_doc, tevkifat_kural_hash = dosya_bul(kok, "tevkifat-kurallar.json")
    randiman_oran_doc, randiman_oran_hash = dosya_bul(kok, "randiman.json")
    randiman_kural_doc, randiman_kural_hash = dosya_bul(kok, "randiman-kurallar.json")
    nace_kural_doc, nace_kural_hash = dosya_bul(kok, "nace-kurallar.json")
    belge_oran_doc, belge_oran_hash = dosya_bul(kok, "zorunlu-belgeler.json")
    belge_kural_doc, belge_kural_hash = dosya_bul(kok, "zorunlu-belgeler-kurallar.json")

    def oran_dict(doc):
        return {k["kod"]: k for k in doc.get("kayitlar", [])}

    kdv_oranlar = oran_dict(kdv_oran_doc)
    otv_oranlar = oran_dict(otv_oran_doc)
    tevkifat_oranlar = oran_dict(tevkifat_oran_doc)
    randiman_oranlar = oran_dict(randiman_oran_doc)
    belge_oranlar = oran_dict(belge_oran_doc)

    def kurallari_hazirla(doc):
        varsayilan, aktif = None, []
        for k in doc.get("kurallar", []):
            if k.get("varsayilan"):
                varsayilan = k
            elif k.get("prefixler"):
                aktif.append(k)
        # Önceliğe ve prefix uzunluğuna göre sıralama için hazırlık
        aktif.sort(key=lambda x: x.get("oncelik", 0), reverse=True)
        return varsayilan, aktif

    kdv_default, kdv_aktif = kurallari_hazirla(kdv_kural_doc)
    otv_default, otv_aktif = kurallari_hazirla(otv_kural_doc)
    tevk_default, tevk_aktif = kurallari_hazirla(tevkifat_kural_doc)

    yapraklar = [k for k in gtip_doc.get("kayitlar", []) if k.get("yaprak") is True]
    print(f"  -> İşlenecek GTİP Yaprağı: {len(yapraklar)}")

    sonuc_kdv, sonuc_otv, sonuc_tevkifat, sonuc_randiman, sonuc_nace, sonuc_tam = [], [], [], [], [], []
    uyarilar = []

    # En spesifik (en uzun prefix) kuralı seçen yardımcı fonksiyon
    def bul_en_spesifik_grup(kod, aktif_kurallar, varsayilan_kural):
        en_uzun = -1
        secilen_grup = None
        
        for k in aktif_kurallar:
            for p in k["prefixler"]:
                clean_p = p.replace(".", "")
                if kod.startswith(clean_p):
                    # Uzunluk önceliği (örn: 2202, 22'den daha spesifiktir)
                    skor = len(clean_p) * 100 + k.get("oncelik", 0)
                    if skor > en_uzun:
                        en_uzun = skor
                        secilen_grup = k["grup"]
                        
        if not secilen_grup and varsayilan_kural:
            secilen_grup = varsayilan_kural["grup"]
        return secilen_grup

    for y in yapraklar:
        kod = str(y.get("kod")).replace(".", "")
        tanim_tr, tanim_en = y.get("tanim_tr"), y.get("tanim_en")

        # --- KDV EŞLEŞTİRME ---
        kdv_grp = bul_en_spesifik_grup(kod, kdv_aktif, kdv_default)
        kdv_data = {"grup": kdv_grp, "oran": None}
        if kdv_grp:
            oran_k = kdv_kural_doc["gruplar"].get(kdv_grp, {}).get("oran_kodu")
            if oran_k in kdv_oranlar:
                kdv_data["oran"] = kdv_oranlar[oran_k]["oran"]
        sonuc_kdv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **kdv_data})

        # --- ÖTV EŞLEŞTİRME ---
        otv_grp = bul_en_spesifik_grup(kod, otv_aktif, otv_default)
        otv_data = {"grup": otv_grp, "oran": None}
        if otv_grp:
            oran_k = otv_kural_doc["gruplar"].get(otv_grp, {}).get("oran_kodu")
            if oran_k in otv_oranlar:
                kaynak_veri = otv_oranlar[oran_k]
                # Sadece arayüz ve hesaplama için gerekli olan temel alanları kopyala
                izin_verilen_alanlar = ("liste", "vergi_tipi", "oran", "matrah_dilimleri")
                for alan in izin_verilen_alanlar:
                    if alan in kaynak_veri:
                        otv_data[alan] = kaynak_veri[alan]
        # Kalem bazlı tutar/oran: GTİP'e en uzun prefix ile uyan kalemi seç
        kalemler = otv_data.pop("kalemler", None)
        if kalemler:
            en_iyi, en_uzun_k = None, -1
            for kl in kalemler:
                kp = str(kl.get("gtip", "")).replace(".", "")
                if kp and kod.startswith(kp) and len(kp) > en_uzun_k:
                    en_iyi, en_uzun_k = kl, len(kp)
            if en_iyi:
                otv_data["kalem"] = en_iyi["gtip"]
                for alan in ("oran", "asgari_maktu", "maktu"):
                    if alan in en_iyi:
                        otv_data[alan] = en_iyi[alan]
            else:
                uyarilar.append(f"{kod} ({(tanim_tr or '')[:45]}): {otv_grp} grubunda uyan kalem yok")
        sonuc_otv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **otv_data})

        # --- TEVKİFAT EŞLEŞTİRME ---
        tevk_grp = bul_en_spesifik_grup(kod, tevk_aktif, tevk_default)
        tevk_data = {"grup": tevk_grp, "oran": None}
        if tevk_grp and tevk_grp != "tevkifat_yok":
            oran_k = tevkifat_kural_doc["gruplar"].get(tevk_grp, {}).get("oran_kodu")
            if oran_k in tevkifat_oranlar:
                kaynak_veri = tevkifat_oranlar[oran_k]
                tevk_data["oran"] = kaynak_veri.get("oran")
                tevk_data["oran_kesir"] = kaynak_veri.get("oran_kesir")
                tevk_data["ad_tr"] = kaynak_veri.get("ad_tr")
                tevk_data["kanun_dayanagi"] = kaynak_veri.get("kanun_dayanagi")
        
        # Listeye ekleme kısmı (Bunu silmediğinizden emin olun!)
        sonuc_tevkifat.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **tevk_data})

        # --- NACE EŞLEŞTİRME ---
        nace_kodu = None
        en_uzun_nace = -1
        for k in nace_kural_doc.get("kurallar", []):
            for p in k.get("prefixler", []):
                clean_p = p.replace(".", "")
                if kod.startswith(clean_p) and len(clean_p) > en_uzun_nace:
                    en_uzun_nace = len(clean_p)
                    nace_kodu = k["nace_kodu"]
        
        nace_data = {"kod": nace_kodu} if nace_kodu else None

        # --- ZORUNLU BELGE EŞLEŞTİRME ---
        belge_listesi = []
        for k in belge_kural_doc.get("kurallar", []):
            for p in k.get("prefixler", []):
                clean_p = str(p).replace(".", "")
                if kod.startswith(clean_p):
                    # Eşleşen belgelerin detaylarını oran dosyasından çek
                    for b_kod in k.get("belge_kodlari", []):
                        if b_kod in belge_oranlar:
                            belge_listesi.append(belge_oranlar[b_kod])
                    break # Aynı kurala birden fazla uymasın
        
        # YENİ EKLENEN: NACE listesine ekleme yapılıyor!
        sonuc_nace.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, "nace": nace_data})

        # --- RANDIMAN EŞLEŞTİRME ---
        rd_girdi, rd_cikti = [], []
        for k in randiman_kural_doc.get("kurallar", []):
            r_kod = k.get("randiman_kodu")
            r_veri = randiman_oranlar.get(r_kod, {})
            
            # 1. Girdi (Ham madde) kontrolü
            if any(kod.startswith(p.replace(".", "")) for p in k.get("girdi_prefixler", [])):
                rd_girdi.append({
                    "kural_kod": k["kod"],
                    "cikti_prefixler": k.get("cikti_prefixler"),
                    "randiman_orani": r_veri.get("randiman_orani"),
                    "fire_orani": r_veri.get("fire_orani"),
                    "ad_tr": r_veri.get("ad_tr"),
                    "ad_en": r_veri.get("ad_en"),
                    "birim": r_veri.get("birim"),
                    "aciklama_tr": r_veri.get("aciklama_tr"),
                    "aciklama_en": r_veri.get("aciklama_en")
                })
            
            # 2. Çıktı (Mamul) kontrolü
            if any(kod.startswith(p.replace(".", "")) for p in k.get("cikti_prefixler", [])):
                rd_cikti.append({
                    "kural_kod": k["kod"],
                    "girdi_prefixler": k.get("girdi_prefixler"),
                    "randiman_orani": r_veri.get("randiman_orani"),
                    "fire_orani": r_veri.get("fire_orani"),
                    "ad_tr": r_veri.get("ad_tr"),
                    "ad_en": r_veri.get("ad_en"),
                    "birim": r_veri.get("birim"),
                    "aciklama_tr": r_veri.get("aciklama_tr"),
                    "aciklama_en": r_veri.get("aciklama_en")
                })
        
        rd_data = {"girdi_oldugu_kurallar": rd_girdi, "cikti_oldugu_kurallar": rd_cikti}
        sonuc_randiman.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **rd_data})

        # --- TAM LİSTE (gtip-tam) ---
        sonuc_tam.append({
            "kod": kod,
            "tanim_tr": tanim_tr,
            "tanim_en": tanim_en,
            "kdv": kdv_data,
            "otv": otv_data,
            "tevkifat": tevk_data,
            "nace": nace_data,
            "randiman": rd_data,
            "belgeler": belge_listesi
        })

        # --- SANITY CHECK ---
        sanity_check(kod, tanim_tr or "", kdv_data, otv_data, uyarilar)

    # Uyarıları özetle
    if uyarilar:
        print(f"\n  [UYARI] {len(uyarilar)} semantik eşleştirme sorunu tespit edildi:")
        for u in uyarilar[:30]:
            print(f"    - {u}")
        if len(uyarilar) > 30:
            print(f"    ... ve {len(uyarilar) - 30} uyarı daha (yukarıdaki gibi)")
        print()

    bugun = datetime.date.today()
    simdi = datetime.datetime.now(datetime.timezone.utc).isoformat()

    nace_meta = nace_kural_doc.get("meta", {})
    
    uretim_meta = {
        "yayinci": kdv_kural_doc["meta"]["yayinci"],
        # Kaynakları ve mevzuatları birleştir
        "kaynaklar": (
            kdv_kural_doc["meta"].get("kaynaklar", []) + 
            otv_kural_doc["meta"].get("kaynaklar", []) + 
            nace_meta.get("kaynaklar", [])
        ),
        "mevzuat_ref": (
            kdv_kural_doc["meta"].get("mevzuat_ref", []) + 
            otv_kural_doc["meta"].get("mevzuat_ref", []) + 
            nace_meta.get("mevzuat_ref", [])
        ),
        "uretim": {
            "ham_kaynaklar": [
                {"servis_kod": "gtip-kodlari", "surum": gtip_doc.get("meta", {}).get("surum"), "checksum": gtip_hash},
                {"servis_kod": "kdv-oranlari", "surum": kdv_oran_doc.get("meta", {}).get("surum"), "checksum": kdv_oran_hash},
                {"servis_kod": "otv-oranlari", "surum": otv_oran_doc.get("meta", {}).get("surum"), "checksum": otv_oran_hash},
                {"servis_kod": "tevkifat-oranlari", "surum": tevkifat_oran_doc.get("meta", {}).get("surum"), "checksum": tevkifat_oran_hash},
                {"servis_kod": "randiman", "surum": randiman_oran_doc.get("meta", {}).get("surum"), "checksum": randiman_oran_hash},
                {"servis_kod": "nace-kurallar", "surum": nace_meta.get("surum"), "checksum": nace_kural_hash}, # YENİ EKLENDİ
            ],
            "kural_seti": {"kod": "coklu-kural", "surum": bugun.strftime("%Y.%m.%d")},
            "uretim_zamani": simdi,
            "eslesme_ozeti": {
                "toplam": len(yapraklar), 
                "eslesen": len(yapraklar) - sum(1 for r in sonuc_kdv if not r["grup"]), 
                "eslesmeyen": sum(1 for r in sonuc_kdv if not r["grup"])
            },
        },
    }

    # 1. Klasörlere (Fasıl bazında) yazma işlemleri
    parcala_ve_yaz(kok, "gtip-kdv", "GTİP KDV Eşleşmesi", "GTIP VAT Mapping", sonuc_kdv, uretim_meta)
    parcala_ve_yaz(kok, "gtip-otv", "GTİP ÖTV Eşleşmesi", "GTIP SCT Mapping", sonuc_otv, uretim_meta)
    parcala_ve_yaz(kok, "gtip-tevkifat", "GTİP Tevkifat Eşleşmesi", "GTIP Withholding Mapping", sonuc_tevkifat, uretim_meta)
    parcala_ve_yaz(kok, "gtip-randiman", "GTİP Randıman Eşleşmesi", "GTIP Yield Mapping", sonuc_randiman, uretim_meta)
    parcala_ve_yaz(kok, "gtip-nace", "GTİP NACE Eşleşmesi", "GTIP NACE Mapping", sonuc_nace, uretim_meta) # YENİ EKLENDİ
    parcala_ve_yaz(kok, "gtip-tam", "GTİP Tüm Vergiler", "GTIP All Taxes", sonuc_tam, uretim_meta)

    # 2. Tek Dosyaya (Tümünü kapsayan) yazma işlemleri
    tum_veriyi_yaz(kok, "gtip-kdv", "GTİP KDV Eşleşmesi (Tümü)", "GTIP VAT Mapping (All)", sonuc_kdv, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-otv", "GTİP ÖTV Eşleşmesi (Tümü)", "GTIP SCT Mapping (All)", sonuc_otv, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-tevkifat", "GTİP Tevkifat Eşleşmesi (Tümü)", "GTIP Withholding Mapping (All)", sonuc_tevkifat, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-randiman", "GTİP Randıman Eşleşmesi (Tümü)", "GTIP Yield Mapping (All)", sonuc_randiman, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-nace", "GTİP NACE Eşleşmesi (Tümü)", "GTIP NACE Mapping (All)", sonuc_nace, uretim_meta) # YENİ EKLENDİ
    tum_veriyi_yaz(kok, "gtip-tam", "GTİP Tüm Vergiler (Tümü)", "GTIP All Taxes (All)", sonuc_tam, uretim_meta)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default=None)
    ap.add_argument("--yayinla", action="store_true", help="Sadece derler, pdaas.py'yi çağırmaz")
    args = ap.parse_args()

    kok = Path(args.kok).expanduser().resolve() if args.kok else Path(__file__).resolve().parent.parent

    # 1. ADIM: Eşleştirmeleri yap (derle.py)
    print("\n[1/2] GTİP eşleştirmeleri yapılıyor...")
    try:
        eslesme_yap(kok)
    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1

    # 2. ADIM: Katalogu ve arşivleri güncelle (pdaas.py)
    if not args.yayinla:
        print("\n[2/2] Katalog güncelleniyor ve dosyalar doğrulanıyor (pdaas.py)...")
        sonuc = subprocess.run([sys.executable, str(kok / "araclar" / "pdaas.py"), "--force"])
        if sonuc.returncode != 0:
            print("pdaas.py çalışırken hata oluştu.", file=sys.stderr)
            return sonuc.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())