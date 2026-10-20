#!/usr/bin/env python3
"""
birlestir.py — fasıl dosyalarını tek gtip-kodlari.json'da birleştirir.

Girdi:
    ham/surumler/gtip-kodlari/2026.01.01/fasil/*.json   (her biri parca.tur="fasil")

Çıktı:
    ham/gtip-kodlari.json

Yaptığı:
    - Her fasıl dosyasını okur
    - Her faslın ust_kod'una göre BOLUM_TANIMLARI'ndan seviye-1 kaydı üretir
    - Bölümün sira'sı = o bölümün ilk faslının sira'sından 1 eksiği
    - Tüm kayıtları sira'ya göre sıralar
    - checksum = kanonik JSON (excel_to_json.py'deki ozet() ile birebir aynı)

Kullanım:
    python araclar/birlestir.py
    python araclar/birlestir.py --klasor /path/to/fasil --cikti /path/out.json
    python araclar/birlestir.py --kati      # uyarıları da hata say (CI için)
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VARSAYILAN_KLASOR = KOK / "ham" / "gtip-kodlari" / "fasil"
VARSAYILAN_CIKTI   = KOK / "ham" / "gtip-kodlari.json"


# Bölüm tanımları — fasıl dosyaları birleştirilirken sentetik seviye-1 kayıt üretilir.
# 21 bölüm tamamlandığında bu dict 21 satır olur; başka dosyaya gerek yok.
BOLUM_TANIMLARI = {
    "I":  {"tr": "CANLI HAYVANLAR VE HAYVANSAL ÜRÜNLER", "en": "LIVE ANIMALS AND ANIMAL PRODUCTS"},
    "II": {"tr": "BİTKİSEL ÜRÜNLER",                     "en": "VEGETABLE PRODUCTS"},
}


def ozet(veri) -> str:
    """excel_to_json.py'deki ozet() ile BİREBİR aynı olmalı."""
    b = json.dumps(veri, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Fasıl dosyalarını birleştir")
    ap.add_argument("--klasor", type=Path, default=VARSAYILAN_KLASOR)
    ap.add_argument("--cikti",  type=Path, default=VARSAYILAN_CIKTI)
    ap.add_argument("--kati", action="store_true", help="Uyarıları da hata say")
    args = ap.parse_args()

    if not args.klasor.exists():
        print(f"HATA: klasör yok: {args.klasor}")
        return 2

    dosyalar = sorted(args.klasor.glob("*.json"))
    if not dosyalar:
        print(f"HATA: {args.klasor} içinde json yok")
        return 2

    tum_kayitlar: list[dict] = []
    meta_sablon: dict | None = None
    hatalar: list[str] = []
    uyarilar: list[str] = []
    onceki_sira = 0
    onceki_dosya = ""

    for dosya in dosyalar:
        try:
            with dosya.open(encoding="utf-8") as f:
                veri = json.load(f)
        except json.JSONDecodeError as e:
            hatalar.append(f"{dosya.name}: JSON hatası — {e}")
            continue

        meta = veri.get("meta", {})
        parca = meta.get("parca")
        if not parca or parca.get("tur") != "fasil":
            hatalar.append(f"{dosya.name}: parca.tur != 'fasil'")
            continue

        if meta_sablon is None:
            meta_sablon = meta.copy()

        kayitlar = veri.get("kayitlar", [])
        if not kayitlar:
            uyarilar.append(f"{dosya.name}: kayitlar boş")
            continue

        # Sira monotonluğu (dosya içinde ve dosyalar arası)
        for k in kayitlar:
            s = k.get("sira", 0)
            if s <= onceki_sira:
                hatalar.append(f"{dosya.name}: sira {s} önceki {onceki_sira}'dan büyük değil")
                break
            if onceki_sira and s != onceki_sira + 1:
                uyarilar.append(
                    f"{onceki_dosya} → {dosya.name}: sira atlaması ({onceki_sira} → {s}, {s - onceki_sira - 1} boşluk)"
                )
            onceki_sira = s
        onceki_dosya = dosya.name
        tum_kayitlar.extend(kayitlar)

    if hatalar:
        print(f"HATALAR ({len(hatalar)}):")
        for h in hatalar:
            print(f"  ✖  {h}")
        return 1

    # Kullanılan bölümleri çıkar
    kullanilan = {k["ust_kod"] for k in tum_kayitlar if k.get("seviye") == 2 and k.get("ust_kod")}
    eksik_bolum = kullanilan - BOLUM_TANIMLARI.keys()
    if eksik_bolum:
        hatalar.append(f"BOLUM_TANIMLARI'nda tanımsız bölümler: {sorted(eksik_bolum)}")
        for h in hatalar:
            print(f"  ✖  {h}")
        return 1

    # Her bölüm için sentetik seviye-1 kayıt üret
    bolum_siralari: dict[str, int] = {}
    for b in kullanilan:
        ilk_fasil = min(
            (k["sira"] for k in tum_kayitlar if k.get("ust_kod") == b and k.get("seviye") == 2),
            default=None,
        )
        if ilk_fasil is None:
            hatalar.append(f"Bölüm {b!r} için hiç fasıl yok")
            continue
        bolum_siralari[b] = ilk_fasil - 1

    for b, s in bolum_siralari.items():
        tanim = BOLUM_TANIMLARI[b]
        tum_kayitlar.append({
            "kod": b,
            "ust_kod": None,
            "seviye": 1,
            "seviye_adi": "bolum",
            "sira": s,
            "yaprak": False,
            "tanim_tr": tanim["tr"],
            "tanim_en": tanim["en"],
            "olcu_birimi": None,
        })

    # Sira bazında sırala
    tum_kayitlar.sort(key=lambda k: k["sira"])

    # Rapor
    yaprak = sum(1 for k in tum_kayitlar if k.get("yaprak"))
    print("=" * 70)
    print(f"Birleştirme raporu — {len(dosyalar)} fasıl dosyası, {len(kullanilan)} bölüm")
    print("=" * 70)
    print(f"Toplam kayıt : {len(tum_kayitlar):>6}")
    print(f"Yaprak       : {yaprak:>6}")
    print(f"Bölümler     : {sorted(kullanilan)}")
    print(f"Bölüm sira   : {dict(sorted(bolum_siralari.items()))}")
    print()
    if uyarilar:
        print(f"UYARILAR ({len(uyarilar)}):")
        for u in uyarilar:
            print(f"  ⚠  {u}")
        print()
        if args.kati:
            print("--kati modunda uyarı = hata, çıkılıyor.")
            return 1

    # Meta hazırla
    if meta_sablon is None:
        print("HATA: hiçbir dosyadan meta okunamadı")
        return 2
    meta = meta_sablon.copy()
    meta.pop("parca", None)
    meta["checksum"]["deger"] = ozet(tum_kayitlar)

    sonuc = {"meta": meta, "kayitlar": tum_kayitlar}
    args.cikti.parent.mkdir(parents=True, exist_ok=True)
    with args.cikti.open("w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"YAZILDI   {args.cikti}")
    print(f"Checksum  {meta['checksum']['deger']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())