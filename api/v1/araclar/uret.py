#!/usr/bin/env python3
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HAM = KOK / "ham"
KONSOLIDE = KOK / "konsolide"

KAYNAKLAR = [
    "gtip-kodlari.json",
    "kdv-oranlari.json",
    "otv-oranlari.json",
    "kdv-tevkifat-oranlari.json",
    "kdv-otv-esleme.json"
]

def yukle(ad: str) -> dict:
    with (HAM / ad).open(encoding="utf-8") as f:
        return json.load(f)

def kanonik_hash(obj) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def en_uzun_prefix(gtip: str, kurallar: list[dict], tip: str) -> dict | None:
    """GTİP kodu için kurallar arasından en uzun prefix'e sahip olanı bul."""
    en_iyi = None
    en_uzun = -1
    for kural in kurallar:
        if kural.get("tip") != tip:
            continue
        kosul = kural.get("kosul", {})
        if kosul.get("operator") != "prefix":
            continue
        prefix = kosul.get("deger", "")
        if prefix and gtip.startswith(prefix):
            if len(prefix) > en_uzun:
                en_uzun = len(prefix)
                en_iyi = kural
    return en_iyi

def main():
    # 1. Girdileri kontrol et ve yükle
    eksikler = [ad for ad in KAYNAKLAR if not (HAM / ad).exists()]
    if eksikler:
        print("HATA: Eksik ham dosyalar:")
        for ad in eksikler:
            print(f" - ham/{ad}")
        return 1

    gtip_veri = yukle("gtip-kodlari.json")
    kdv_veri = yukle("kdv-oranlari.json")
    otv_veri = yukle("otv-oranlari.json")
    tev_veri = yukle("kdv-tevkifat-oranlari.json")
    esleme_veri = yukle("kdv-otv-esleme.json")

    # Checksum kontrolü
    kaynak_hash = {}
    for ad in KAYNAKLAR:
        veri = yukle(ad)
        deger = veri.get("meta", {}).get("checksum", {}).get("deger")
        if not deger:
            print(f"HATA: ham/{ad} dosyasının checksum'ı hesaplanmamış. Önce dogrula.py çalıştırın.")
            return 1
        kaynak_hash[ad] = deger

    # İndeksler
    kdv_idx = {k["kod"]: k for k in kdv_veri.get("kayitlar", [])}
    otv_idx = {k["kod"]: k for k in otv_veri.get("kayitlar", [])}
    tev_idx = {k["kod"]: k for k in tev_veri.get("kayitlar", [])}
    kurallar = esleme_veri.get("kurallar", [])

    # 2. Konsolide kayıtları üret
    kayitlar = []
    yapraklar = [k for k in gtip_veri.get("kayitlar", []) if k.get("yaprak")]
    
    for g in yapraklar:
        gtip = g["kod"]
        
        # KDV Eşleşmesi
        kdv_s = None
        kdv_k = en_uzun_prefix(gtip, kurallar, "kdv")
        if kdv_k:
            sonuc = kdv_k.get("sonuc", {})
            oran = sonuc.get("oran", 0.20) # varsayılan genel oran
            kdv_s = {
                "oran": oran,
                "kategori": sonuc.get("liste", "genel"),
                "kaynak": {"servis": "kdv-oranlari", "surum": kdv_veri["meta"]["surum"]["surum"], "kayit": sonuc.get("liste", "genel")}
            }
        
        # ÖTV Eşleşmesi
        otv_s = None
        otv_k = en_uzun_prefix(gtip, kurallar, "otv")
        if otv_k:
            sonuc = otv_k.get("sonuc", {})
            otv_s = {
                "kod": sonuc.get("kod"),
                "vergi_tipi": sonuc.get("vergi_tipi"),
                "kaynak": {"servis": "otv-oranlari", "surum": otv_veri["meta"]["surum"]["surum"], "kayit": sonuc.get("kod")}
            }
        
        # Tevkifat Eşleşmesi
        tev_s = None
        tev_k = en_uzun_prefix(gtip, kurallar, "tevkifat")
        if tev_k:
            sonuc = tev_k.get("sonuc", {})
            tev_s = {
                "kod": sonuc.get("kod"),
                "oran": sonuc.get("oran"),
                "kaynak": {"servis": "kdv-tevkifat-oranlari", "surum": tev_veri["meta"]["surum"]["surum"], "kayit": sonuc.get("kod")}
            }

        kayitlar.append({
            "gtip": gtip,
            "ad_tr": g.get("tanim_tr", ""),
            "ad_en": g.get("tanim_en", ""),
            "kdv": kdv_s,
            "otv": otv_s,
            "tevkifat": tev_s
        })

    # 3. Yeni Meta ve Uretim bilgisi
    simdi = datetime.now(timezone.utc).isoformat(timespec="seconds")
    yeni_meta = {
        "$schema": "https://pdaas.com.tr/api/v1/meta/schema/pdaas-meta-1.3.0.json",
        "schema_surumu": "1.3.0",
        "servis": {
            "kod": "kdv-otv-tevkifat",
            "ad": {"tr": "KDV/ÖTV/Tevkifat Bütünleşik Görünüm", "en": "Consolidated VAT/SCT/Withholding View"}
        },
        "yayinci": {
            "kod": "gib",
            "ad": {"tr": "T.C. Hazine ve Maliye Bakanlığı", "en": "Republic of Türkiye Ministry of Treasury and Finance"},
            "birim": {"tr": "Gelir İdaresi Başkanlığı", "en": "Revenue Administration"},
            "konsorsiyum": False,
            "kurumlar": ["gib"]
        },
        "katman": "konsolide",
        "yapi": {
            "tip": "liste",
            "kod_sistemi": "gtip",
            "join": {"alan": "gtip", "yontem": "tam"},
            "kapsam": ["urun", "vergi"]
        },
        "surum": {
            "surum": "2026.01.02", 
            "dosya_surumu": "1.0.0",
            "onceki": None,
            "guncelleme": "2026-01-02"
        },
        "zaman": {"zaman_bazli": False, "gecerlilik_baslangic": None, "gecerlilik_bitis": None},
        "kaynaklar": [{"kod": "gib-birlesik", "ad": {"tr": "Birleşik Görünüm", "en": "Consolidated View"}, "tur": "mevzuat", "kurum_kod": "gib", "url": None, "erisim_tarihi": None}],
        "mevzuat_ref": [],
        "yayin_durumu": "yayinda",
        "checksum": {"algoritma": "sha256", "deger": kanonik_hash(kayitlar), "kapsam": "kayitlar"},
        "uretim": {
            "ham_kaynaklar": [{"servis": ad.replace(".json", ""), "surum": yukle(ad)["meta"]["surum"]["surum"], "checksum": kaynak_hash[ad]} for ad in KAYNAKLAR if ad != "kdv-otv-esleme.json"],
            "kural_seti": {"kod": "kdv-otv-esleme", "surum": esleme_veri["meta"]["surum"]["surum"]},
            "eslesme_ozeti": {"toplam": len(kayitlar), "eslesen": len(kayitlar), "eslesmeyen": 0}
        }
    }

    # 4. Yaz
    KONSOLIDE.mkdir(parents=True, exist_ok=True)
    hedef = KONSOLIDE / "kdv-otv-tevkifat.json"
    with hedef.open("w", encoding="utf-8") as f:
        json.dump({"meta": yeni_meta, "kayitlar": kayitlar}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"OK   {hedef.relative_to(KOK)}")
    print(f"     {len(kayitlar)} konsolide kayıt üretildi.")
    print(f"     Checksum: {yeni_meta['checksum']['deger'][:16]}...")
    return 0

if __name__ == "__main__":
    sys.exit(main())