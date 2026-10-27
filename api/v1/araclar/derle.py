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
    yol = kok / dosya_adi
    if not yol.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {yol}")
    doc = yukle(yol)
    return doc, sha256(doc.get("kayitlar", doc.get("kurallar", doc)))


def sanity_check(kod, tanim_tr, kdv_data, otv_data, uyarilar):
    kdv_grp = (kdv_data or {}).get("grup") or ""
    kdv_oran = (kdv_data or {}).get("oran")
    otv_grp = (otv_data or {}).get("grup") or ""

    if kod.startswith(("2203", "2204", "2205", "2206", "2207", "2208")):
        if otv_grp.startswith("OTV-III-B") or "Tutun" in otv_grp:
            uyarilar.append(f"{kod} ({tanim_tr[:45]}): alkollü içecek tütün grubunda -> {otv_grp}")
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
    if kod.startswith(("8703", "340", "481810", "481820", "481830")) and kdv_oran is not None and kdv_oran != 0.20:
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): KDV %{kdv_oran*100:.0f} (genel %20 olmalı; grup={kdv_grp})")
    if kod.startswith(("2402", "2403")) and otv_grp != "OTV-III-B-Tutun":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): tütün grubunda değil -> {otv_grp}")
    if (kod.startswith(("240411", "240412", "240419", "240491", "240499")) and otv_grp != "OTV-III-B-Tutun"):
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): 2404 nikotin/tütün ürünü tütün grubunda değil -> {otv_grp}")
    if kod.startswith("240492") and otv_grp and otv_grp != "otv_yok":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): transdermal nikotin bandı ÖTV'ye tabi olmamalı -> {otv_grp}")
    if kod.startswith("8517") and kdv_oran is not None and kdv_oran < 0.20:
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): KDV %{kdv_oran*100:.0f} (genel %20 olmalı; grup={kdv_grp})")
    if kod.startswith(("2710198", "2710199")) and otv_grp == "OTV-I-A-Akaryakit":
        uyarilar.append(f"{kod} ({tanim_tr[:45]}): madeni yağ akaryakıt grubunda")


def belgeleri_bul(kod, belge_kural_doc, belge_oranlar, kod_sistemi="gtip"):
    if kod_sistemi == "nace":
        prefix_alani = "nace_prefixler"
    elif kod_sistemi == "cpc":
        prefix_alani = "cpc_prefixler"
    elif kod_sistemi == "isco":  # <-- BURAYI EKLEYİN
        prefix_alani = "isco_prefixler"
    else:
        prefix_alani = "gtip_prefixler"
        
    sonuc = {"yurtici": [], "ithalat": [], "ihracat": []}
    kurallar = sorted(belge_kural_doc.get("kurallar", []), key=lambda x: x.get("oncelik", 0), reverse=True)
    
    for k in kurallar:
        eslesti = False
        for p in k.get(prefix_alani, []):
            # Noktaları temizleyerek eşleştirme yap (NACE ve GTİP için)
            p_str = str(p).replace(".", "")
            if p_str and kod.startswith(p_str):
                eslesti = True
                break
        
        if not eslesti: continue
            
        islem_tipleri = k.get("islem_tipleri", ["yurtici", "ithalat", "ihracat"])
        
        # NACE ise sadece yurtiçi işlemini dikkate al (NACE ihracat/ithalat gerektirmez)
        if kod_sistemi == "nace" and "yurtici" not in islem_tipleri:
            continue

        for islem in islem_tipleri:
            if islem in sonuc:
                for b_kod in k.get("belge_kodlari", []):
                    if b_kod in belge_oranlar:
                        belge_verisi = belge_oranlar[b_kod].copy()
                        if "ek_kriterler" in k: belge_verisi["ek_kriterler"] = k["ek_kriterler"]
                        if "kosullu" in k: belge_verisi["kosullu"] = k["kosullu"]
                        
                        mevcut_kodlar = [b.get("kod") for b in sonuc[islem]]
                        if b_kod not in mevcut_kodlar:
                            sonuc[islem].append(belge_verisi)
    return sonuc


def parcala_ve_yaz(kok, servis_kod, ad_tr, ad_en, kayitlar, meta_kaynak, kod_sistemi="gtip"):
    prefix_uzunluk = 1 if kod_sistemi in ("cpc", "nace") else 2
    klasor_adi = "bolum" if kod_sistemi in ("cpc", "nace") else "fasil"
    hedef_klasor = kok / servis_kod
    alt_klasor = hedef_klasor / klasor_adi

    gruplar = {}
    for k in kayitlar:
        kod_str = str(k.get("kod", "")).replace(".", "")
        if not kod_str:
            kod_str = "0"
        grup = kod_str[:prefix_uzunluk]
        gruplar.setdefault(grup, []).append(k)

    bugun = datetime.date.today()
    temel_meta = {
        "schema_surumu": "1.0.0",
        "servis": {"kod": servis_kod, "ad": {"tr": ad_tr, "en": ad_en}},
        "katman": "konsolide",
        "yapi": {"tip": "liste", "kod_sistemi": kod_sistemi, "kapsam": ["vergi", "ticaret"]},
        "surum": bugun.strftime("%Y.%m.%d"),
        "guncelleme": bugun.isoformat(),
        "yayin_durumu": "yayinda",
        "zaman": {"bazli": False, "baslangic": None, "bitis": None},
        "yayinci": meta_kaynak["yayinci"],
        "kaynaklar": meta_kaynak.get("kaynaklar", []),
        "mevzuat_ref": meta_kaynak.get("mevzuat_ref", []),
        "uretim": meta_kaynak["uretim"],
    }

    for grup, f_kayitlar in gruplar.items():
        parca_meta = dict(temel_meta)
        parca_meta["parca"] = {"tur": klasor_adi, "kod": grup, "ana_dosya": "index.json"}
        yaz(alt_klasor / f"{grup}.json", {"meta": parca_meta, "kayitlar": f_kayitlar})

    index_meta = dict(temel_meta)
    index_meta["parca"] = {"tur": "index", "kod": "index", "ana_dosya": f"{servis_kod}.json"}
    yaz(hedef_klasor / "index.json", {
        "meta": index_meta,
        "parcalar": [
            {"kod": grup, "kayit_sayisi": len(f_kayitlar), "dosya": f"{klasor_adi}/{grup}.json"}
            for grup, f_kayitlar in sorted(gruplar.items())
        ],
    })
    print(f"  -> {servis_kod} (Klasör): {len(gruplar)} {klasor_adi}.")


def tum_veriyi_yaz(kok, servis_kod, ad_tr, ad_en, kayitlar, meta_kaynak, kod_sistemi="gtip"):
    bugun = datetime.date.today()
    temel_meta = {
        "schema_surumu": "1.0.0",
        "servis": {"kod": servis_kod, "ad": {"tr": ad_tr, "en": ad_en}},
        "katman": "konsolide",
        "yapi": {"tip": "liste", "kod_sistemi": kod_sistemi, "kapsam": ["vergi", "ticaret"]},
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

def sgk_prim_hesapla(kod, sgk_prim_doc):
    # SGK Prim oranları dosyasından genel oranları çek
    oran_dict = {k["kod"]: k for k in sgk_prim_doc.get("kayitlar", [])}
    
    isci = oran_dict.get("sgk_isci_primi", {}).get("oran", 14.0) + oran_dict.get("issizlik_isci_primi", {}).get("oran", 1.0)
    isveren_tevkisiz = oran_dict.get("toplam_isveren_primi_tesviksiz", {}).get("oran", 23.75)
    
    # NACE koduna göre imalat sektörü mü kontrol et (NACE 10 ile 33 arası imalattır)
    imalat_prefixler = [str(i) for i in range(10, 34)]
    imalat = any(kod.startswith(p) for p in imalat_prefixler)
    
    if imalat:
        isveren_tevkisli = oran_dict.get("toplam_isveren_primi_5puanli_imalat", {}).get("oran", 18.75)
        tesvik_adi = "5510 — Beş Puanlık Prim İndirimi (İmalat)"
    else:
        isveren_tevkisli = oran_dict.get("toplam_isveren_primi_diger_2puan", {}).get("oran", 21.75)
        tesvik_adi = "5510 — İki Puanlık Prim İndirimi (İmalat Dışı)"
        
    return {
        "isci_pay": isci,
        "isveren_pay_tevkisiz": isveren_tevkisiz,
        "isveren_pay_tevkisli": isveren_tevkisli,
        "tesvik_kodu": "5510",
        "tesvik_adi": tesvik_adi
    }

def vergi_verisi_olustur(kural, oran_dict, fallback_grp="genel"):
    if not kural:
        return {"grup": None, "oran": None, "vergi_turu": None, "islem_tipleri": [], 
                "alici_tipleri": [], "satici_tipleri": [], "ek_kriterler": {}, 
                "istisna": False, "kosullu": False}

    grp = kural.get("grup", fallback_grp)
    veri = {
        "grup": grp,
        "vergi_turu": kural.get("vergi_turu"),
        "oran": kural.get("oran"),
        "islem_tipleri": kural.get("islem_tipleri", []),
        "alici_tipleri": kural.get("alici_tipleri", []),
        "satici_tipleri": kural.get("satici_tipleri", []),
        "ek_kriterler": kural.get("ek_kriterler", {}),
        "istisna": kural.get("istisna", False),
        "istisna_tipi": kural.get("istisna_tipi"),
        "kosullu": kural.get("kosullu", False)
    }

    oran_k = kural.get("oran_kodu") or grp
    if oran_k in oran_dict:
        kaynak = oran_dict[oran_k]
        if veri["oran"] is None:
            veri["oran"] = kaynak.get("oran")
        
        for alan in ("liste", "vergi_tipi", "matrah_dilimleri", "maktu", "asgari_maktu", "kalemler"):
            if alan in kaynak:
                veri[alan] = kaynak[alan]

    return veri


def eslesme_yap(kok):
    print("Konsolide derleme başladı (V1)...")

    gtip_doc, gtip_hash = dosya_bul(kok, "gtip-kodlari.json")
    cpc_doc, cpc_hash = dosya_bul(kok, "cpc-kodlari.json")
    nace_doc, nace_hash = dosya_bul(kok, "nace-kodlari.json")
    
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
    isco_doc, isco_hash = dosya_bul(kok, "isco-kodlari.json")
    sgk_prim_doc, sgk_prim_hash = dosya_bul(kok, "sgk-prim-oranlari.json")
    sgk_tesvik_doc, sgk_tesvik_hash = dosya_bul(kok, "sgk-tesvik-kodlari.json")

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
            elif k.get("gtip_prefixler") or k.get("cpc_prefixler"):
                aktif.append(k)
        aktif.sort(key=lambda x: x.get("oncelik", 0), reverse=True)
        return varsayilan, aktif

    kdv_default, kdv_aktif = kurallari_hazirla(kdv_kural_doc)
    otv_default, otv_aktif = kurallari_hazirla(otv_kural_doc)
    tevk_default, tevk_aktif = kurallari_hazirla(tevkifat_kural_doc)

    yapraklar = [k for k in gtip_doc.get("kayitlar", []) if k.get("yaprak") is True]
    cpc_yapraklar = [k for k in cpc_doc.get("kayitlar", []) if k.get("yaprak") is True]
    print(f"  -> İşlenecek GTİP Yaprağı: {len(yapraklar)}")
    print(f"  -> İşlenecek CPC Yaprağı: {len(cpc_yapraklar)}")
    print(f"  -> İşlenecek NACE Kaydı: {len(nace_doc.get('kayitlar', []))}")

    sonuc_kdv, sonuc_otv, sonuc_tevkifat, sonuc_randiman, sonuc_nace, sonuc_tam = [], [], [], [], [], []
    sonuc_cpc_kdv, sonuc_cpc_otv, sonuc_cpc_tevkifat, sonuc_cpc_tam = [], [], [], []
    sonuc_nace_tam = []
    uyarilar = []

    def bul_en_spesifik_kural(kod, aktif_kurallar, varsayilan_kural, kod_sistemi="gtip"):
        prefix_alani = "cpc_prefixler" if kod_sistemi == "cpc" else "gtip_prefixler"
        en_uzun = -1
        secilen = None
        for k in aktif_kurallar:
            for p in k.get(prefix_alani, []):
                clean_p = str(p).replace(".", "")
                if clean_p and kod.startswith(clean_p):
                    skor = len(clean_p) * 100 + k.get("oncelik", 0)
                    if skor > en_uzun:
                        en_uzun = skor
                        secilen = k
        if not secilen and varsayilan_kural:
            secilen = varsayilan_kural
        return secilen

    # GTİP DÖNGÜSÜ
    for y in yapraklar:
        kod = str(y.get("kod")).replace(".", "")
        tanim_tr, tanim_en = y.get("tanim_tr"), y.get("tanim_en")

        kdv_kural = bul_en_spesifik_kural(kod, kdv_aktif, kdv_default, "gtip")
        kdv_data = vergi_verisi_olustur(kdv_kural, kdv_oranlar)
        sonuc_kdv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **kdv_data})

        otv_kural = bul_en_spesifik_kural(kod, otv_aktif, otv_default, "gtip")
        otv_data = vergi_verisi_olustur(otv_kural, otv_oranlar)
        
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
                uyarilar.append(f"{kod} ({(tanim_tr or '')[:45]}): {otv_data.get('grup')} grubunda uyan kalem yok")
        sonuc_otv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **otv_data})

        tevk_kural = bul_en_spesifik_kural(kod, tevk_aktif, tevk_default, "gtip")
        tevk_data = vergi_verisi_olustur(tevk_kural, tevkifat_oranlar)
        if tevk_kural and tevk_kural.get("oran_kesir"):
            tevk_data["oran_kesir"] = tevk_kural.get("oran_kesir")
        sonuc_tevkifat.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **tevk_data})

        nace_kodu = None
        en_uzun_nace = -1
        for k in nace_kural_doc.get("kurallar", []):
            for p in k.get("gtip_prefixler", []):
                clean_p = p.replace(".", "")
                if clean_p and kod.startswith(clean_p) and len(clean_p) > en_uzun_nace:
                    en_uzun_nace = len(clean_p)
                    nace_kodu = k["nace_kodu"]
        nace_data = {"kod": nace_kodu} if nace_kodu else None

        # --- Zorunlu belge (GTİP için) ---
        belge_listesi = belgeleri_bul(kod, belge_kural_doc, belge_oranlar, "gtip")

        sonuc_nace.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, "nace": nace_data})

        rd_girdi, rd_cikti = [], []
        for k in randiman_kural_doc.get("kurallar", []):
            r_kod = k.get("randiman_kodu")
            r_veri = randiman_oranlar.get(r_kod, {})
            if any(kod.startswith(p.replace(".", "")) for p in k.get("girdi_prefixler", [])):
                rd_girdi.append({
                    "kural_kod": k["kod"], "cikti_prefixler": k.get("cikti_prefixler"),
                    "randiman_orani": r_veri.get("randiman_orani"), "fire_orani": r_veri.get("fire_orani"),
                    "ad_tr": r_veri.get("ad_tr"), "ad_en": r_veri.get("ad_en"),
                    "birim": r_veri.get("birim"), "aciklama_tr": r_veri.get("aciklama_tr"), "aciklama_en": r_veri.get("aciklama_en"),
                })
            if any(kod.startswith(p.replace(".", "")) for p in k.get("cikti_prefixler", [])):
                rd_cikti.append({
                    "kural_kod": k["kod"], "girdi_prefixler": k.get("girdi_prefixler"),
                    "randiman_orani": r_veri.get("randiman_orani"), "fire_orani": r_veri.get("fire_orani"),
                    "ad_tr": r_veri.get("ad_tr"), "ad_en": r_veri.get("ad_en"),
                    "birim": r_veri.get("birim"), "aciklama_tr": r_veri.get("aciklama_tr"), "aciklama_en": r_veri.get("aciklama_en"),
                })

        rd_data = {"girdi_oldugu_kurallar": rd_girdi, "cikti_oldugu_kurallar": rd_cikti}
        sonuc_randiman.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **rd_data})

        sonuc_tam.append({
            "kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en,
            "kdv": kdv_data, "otv": otv_data, "tevkifat": tevk_data,
            "nace": nace_data, "randiman": rd_data, "belgeler": belge_listesi,
        })

        sanity_check(kod, tanim_tr or "", kdv_data, otv_data, uyarilar)
    
    # ISCO DÖNGÜSÜ
    sonuc_isco_tam = []
    for y in isco_doc.get("kayitlar", []):
        kod = str(y.get("kod", "")).replace(".", "")
        tanim_tr, tanim_en = y.get("tanim_tr") or y.get("ad_tr"), y.get("tanim_en") or y.get("ad_en")
        
        # ISCO için sadece belgeleri bul
        belge_listesi = belgeleri_bul(kod, belge_kural_doc, belge_oranlar, "isco")
        
        sonuc_isco_tam.append({
            "kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en,
            "belgeler": belge_listesi,
        })

    # CPC DÖNGÜSÜ
    for y in cpc_yapraklar:
        kod = str(y.get("kod", "")).replace(".", "")
        tanim_tr, tanim_en = y.get("tanim_tr"), y.get("tanim_en")

        kdv_kural = bul_en_spesifik_kural(kod, kdv_aktif, kdv_default, "cpc")
        kdv_data = vergi_verisi_olustur(kdv_kural, kdv_oranlar)
        sonuc_cpc_kdv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **kdv_data})

        otv_kural = bul_en_spesifik_kural(kod, otv_aktif, otv_default, "cpc")
        otv_data = vergi_verisi_olustur(otv_kural, otv_oranlar)
        sonuc_cpc_otv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **otv_data})

        tevk_kural = bul_en_spesifik_kural(kod, tevk_aktif, tevk_default, "cpc")
        tevk_data = vergi_verisi_olustur(tevk_kural, tevkifat_oranlar)
        if tevk_kural and tevk_kural.get("oran_kesir"):
            tevk_data["oran_kesir"] = tevk_kural.get("oran_kesir")
        sonuc_cpc_tevkifat.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **tevk_data})

        nace_kodu = None
        en_uzun_nace = -1
        for k in nace_kural_doc.get("kurallar", []):
            for p in k.get("cpc_prefixler", []):
                clean_p = p.replace(".", "")
                if clean_p and kod.startswith(clean_p) and len(clean_p) > en_uzun_nace:
                    en_uzun_nace = len(clean_p)
                    nace_kodu = k["nace_kodu"]
        nace_data = {"kod": nace_kodu} if nace_kodu else None

        # --- Zorunlu belge (CPC için) ---
        belge_listesi = belgeleri_bul(kod, belge_kural_doc, belge_oranlar, "cpc")

        sonuc_cpc_tam.append({
            "kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en,
            "kdv": kdv_data, "otv": otv_data, "tevkifat": tevk_data, "nace": nace_data,
            "belgeler": belge_listesi,
        })

        # NACE DÖNGÜSÜ
    for y in nace_doc.get("kayitlar", []):
        kod = str(y.get("kod", "")).replace(".", "")
        tanim_tr = y.get("tanim_tr") or y.get("ad_tr")
        tanim_en = y.get("tanim_en") or y.get("ad_en")
        
        belge_listesi = belgeleri_bul(kod, belge_kural_doc, belge_oranlar, "nace")
        
        # --- YENİ: SGK Prim Hesaplaması ---
        sgk_prim = sgk_prim_hesapla(kod, sgk_prim_doc)
        
        sonuc_nace_tam.append({
            "kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en,
            "belgeler": belge_listesi,
            "sgk_prim": sgk_prim
        })

    if uyarilar:
        print(f"\n  [UYARI] {len(uyarilar)} semantik eşleştirme sorunu tespit edildi:")
        for u in uyarilar[:30]: print(f"    - {u}")
        print()

    bugun = datetime.date.today()
    simdi = datetime.datetime.now(datetime.timezone.utc).isoformat()
    nace_meta = nace_kural_doc.get("meta", {})
    toplam = len(yapraklar) + len(cpc_yapraklar)
    eslesmeyen = (sum(1 for r in sonuc_kdv if not r.get("grup")) + sum(1 for r in sonuc_cpc_kdv if not r.get("grup")))
    eslesen = toplam - eslesmeyen

    uretim_meta = {
        "yayinci": kdv_kural_doc["meta"]["yayinci"],
        "kaynaklar": (kdv_kural_doc["meta"].get("kaynaklar", []) + otv_kural_doc["meta"].get("kaynaklar", []) + nace_meta.get("kaynaklar", [])),
        "mevzuat_ref": (kdv_kural_doc["meta"].get("mevzuat_ref", []) + otv_kural_doc["meta"].get("mevzuat_ref", []) + nace_meta.get("mevzuat_ref", [])),
        "uretim": {
            "ham_kaynaklar": [
                {"servis_kod": "gtip-kodlari", "surum": gtip_doc.get("meta", {}).get("surum"), "checksum": gtip_hash},
                {"servis_kod": "cpc-kodlari", "surum": cpc_doc.get("meta", {}).get("surum"), "checksum": cpc_hash},
                {"servis_kod": "nace-kodlari", "surum": nace_doc.get("meta", {}).get("surum"), "checksum": nace_hash},
                {"servis_kod": "kdv-oranlari", "surum": kdv_oran_doc.get("meta", {}).get("surum"), "checksum": kdv_oran_hash},
                {"servis_kod": "otv-oranlari", "surum": otv_oran_doc.get("meta", {}).get("surum"), "checksum": otv_oran_hash},
                {"servis_kod": "tevkifat-oranlari", "surum": tevkifat_oran_doc.get("meta", {}).get("surum"), "checksum": tevkifat_oran_hash},
                {"servis_kod": "randiman", "surum": randiman_oran_doc.get("meta", {}).get("surum"), "checksum": randiman_oran_hash},
                {"servis_kod": "nace-kurallar", "surum": nace_meta.get("surum"), "checksum": nace_kural_hash},
            ],
            "kural_seti": {"kod": "coklu-kural", "surum": bugun.strftime("%Y.%m.%d")},
            "uretim_zamani": simdi,
            "eslesme_ozeti": {"toplam": toplam, "eslesen": eslesen, "eslesmeyen": eslesmeyen},
        },
    }

    # GTİP ÇIKTILARI
    parcala_ve_yaz(kok, "gtip-kdv", "GTİP KDV Eşleşmesi", "GTIP VAT Mapping", sonuc_kdv, uretim_meta, "gtip")
    parcala_ve_yaz(kok, "gtip-otv", "GTİP ÖTV Eşleşmesi", "GTIP SCT Mapping", sonuc_otv, uretim_meta, "gtip")
    parcala_ve_yaz(kok, "gtip-tevkifat", "GTİP Tevkifat Eşleşmesi", "GTIP Withholding Mapping", sonuc_tevkifat, uretim_meta, "gtip")
    parcala_ve_yaz(kok, "gtip-randiman", "GTİP Randıman Eşleşmesi", "GTIP Yield Mapping", sonuc_randiman, uretim_meta, "gtip")
    parcala_ve_yaz(kok, "gtip-nace", "GTİP NACE Eşleşmesi", "GTIP NACE Mapping", sonuc_nace, uretim_meta, "gtip")
    parcala_ve_yaz(kok, "gtip-tam", "GTİP Tüm Vergiler", "GTIP All Taxes", sonuc_tam, uretim_meta, "gtip")

    # CPC ÇIKTILARI
    parcala_ve_yaz(kok, "cpc-kdv", "CPC KDV Eşleşmesi", "CPC VAT Mapping", sonuc_cpc_kdv, uretim_meta, "cpc")
    parcala_ve_yaz(kok, "cpc-otv", "CPC ÖTV Eşleşmesi", "CPC SCT Mapping", sonuc_cpc_otv, uretim_meta, "cpc")
    parcala_ve_yaz(kok, "cpc-tevkifat", "CPC Tevkifat Eşleşmesi", "CPC Withholding Mapping", sonuc_cpc_tevkifat, uretim_meta, "cpc")
    parcala_ve_yaz(kok, "cpc-tam", "CPC Tüm Vergiler", "CPC All Taxes", sonuc_cpc_tam, uretim_meta, "cpc")

    # NACE ÇIKTILARI (Yeni)
    parcala_ve_yaz(kok, "nace-tam", "NACE Tüm Belgeler", "NACE All Documents", sonuc_nace_tam, uretim_meta, "nace")

    parcala_ve_yaz(kok, "isco-tam", "ISCO Tüm Belgeler", "ISCO All Documents", sonuc_isco_tam, uretim_meta, "isco")

    # TEK DOSYA ÇIKTILARI (TÜMÜ)
    tum_veriyi_yaz(kok, "gtip-kdv", "GTİP KDV Eşleşmesi (Tümü)", "GTIP VAT Mapping (All)", sonuc_kdv, uretim_meta, "gtip")
    tum_veriyi_yaz(kok, "gtip-otv", "GTİP ÖTV Eşleşmesi (Tümü)", "GTIP SCT Mapping (All)", sonuc_otv, uretim_meta, "gtip")
    tum_veriyi_yaz(kok, "gtip-tevkifat", "GTİP Tevkifat Eşleşmesi (Tümü)", "GTIP Withholding Mapping (All)", sonuc_tevkifat, uretim_meta, "gtip")
    tum_veriyi_yaz(kok, "gtip-randiman", "GTİP Randıman Eşleşmesi (Tümü)", "GTIP Yield Mapping (All)", sonuc_randiman, uretim_meta, "gtip")
    tum_veriyi_yaz(kok, "gtip-nace", "GTİP NACE Eşleşmesi (Tümü)", "GTIP NACE Mapping (All)", sonuc_nace, uretim_meta, "gtip")
    tum_veriyi_yaz(kok, "gtip-tam", "GTİP Tüm Vergiler (Tümü)", "GTIP All Taxes (All)", sonuc_tam, uretim_meta, "gtip")

    tum_veriyi_yaz(kok, "cpc-kdv", "CPC KDV Eşleşmesi (Tümü)", "CPC VAT Mapping (All)", sonuc_cpc_kdv, uretim_meta, "cpc")
    tum_veriyi_yaz(kok, "cpc-otv", "CPC ÖTV Eşleşmesi (Tümü)", "CPC SCT Mapping (All)", sonuc_cpc_otv, uretim_meta, "cpc")
    tum_veriyi_yaz(kok, "cpc-tevkifat", "CPC Tevkifat Eşleşmesi (Tümü)", "CPC Withholding Mapping (All)", sonuc_cpc_tevkifat, uretim_meta, "cpc")
    tum_veriyi_yaz(kok, "cpc-tam", "CPC Tüm Vergiler (Tümü)", "CPC All Taxes (All)", sonuc_cpc_tam, uretim_meta, "cpc")

    tum_veriyi_yaz(kok, "nace-tam", "NACE Tüm Belgeler (Tümü)", "NACE All Documents (All)", sonuc_nace_tam, uretim_meta, "nace")
    tum_veriyi_yaz(kok, "isco-tam", "ISCO Tüm Belgeler (Tümü)", "ISCO All Documents (All)", sonuc_isco_tam, uretim_meta, "isco")
    


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default=None)
    ap.add_argument("--yayinla", action="store_true", help="Sadece derler, pdaas.py'yi çağırmaz")
    args = ap.parse_args()

    kok = Path(args.kok).expanduser().resolve() if args.kok else Path(__file__).resolve().parent.parent

    print("\n[1/2] GTİP + CPC + NACE eşleştirmeleri yapılıyor (V1)...")
    try:
        eslesme_yap(kok)
    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1

    if not args.yayinla:
        print("\n[2/2] Katalog güncelleniyor ve dosyalar doğrulanıyor (pdaas.py)...")
        sonuc = subprocess.run([sys.executable, str(kok / "araclar" / "pdaas.py"), "--force"])
        if sonuc.returncode != 0:
            print("pdaas.py çalışırken hata oluştu.", file=sys.stderr)
            return sonuc.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())