#!/usr/bin/env python3
"""
checksum.py — PDaaS JSON dosyalarının checksum.deger alanını SHA256 ile doldurur.

Kapsam:
    meta.checksum.kapsam == "kayitlar" -> dosyadaki "kayitlar" dizisi hashlenir
    meta.checksum.kapsam == "kurallar" -> dosyadaki "kurallar" dizisi hashlenir

Kanonik JSON: sort_keys=True, ensure_ascii=False, ayraçsız (',', ':').

Kullanım:
    python araclar/checksum.py                       # tüm ham/ + konsolide/
    python araclar/checksum.py ham/kdv-oranlari.json
    python araclar/checksum.py --check               # sadece kontrol, yazma yok
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent


def hesapla(veri: dict) -> str:
    kapsam = veri["meta"]["checksum"]["kapsam"]
    if kapsam == "kayitlar":
        hedef = veri["kayitlar"]
    elif kapsam == "kurallar":
        hedef = veri["kurallar"]
    else:
        raise ValueError(f"Bilinmeyen kapsam: {kapsam!r}")
    metin = json.dumps(hedef, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def isle(yol: Path, check_only: bool) -> tuple[str, bool]:
    with yol.open(encoding="utf-8") as f:
        veri = json.load(f)

    mevcut = veri["meta"]["checksum"]["deger"]
    yeni = hesapla(veri)

    if check_only:
        if mevcut is None:
            return "EKSIK", False
        return ("OK", True) if mevcut == yeni else ("UYUSMUYOR", False)

    if mevcut == yeni:
        return "ATLANDI", True

    veri["meta"]["checksum"]["deger"] = yeni
    with yol.open("w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return "YAZILDI", True


def main() -> int:
    ap = argparse.ArgumentParser(description="PDaaS checksum hesaplayıcı")
    ap.add_argument("dosyalar", nargs="*", help="Tek tek dosyalar; boşsa tümü")
    ap.add_argument("--check", action="store_true", help="Yazma, sadece kontrol et")
    args = ap.parse_args()

    if args.dosyalar:
        hedefler = [Path(d).resolve() for d in args.dosyalar]
    else:
        hedefler = (
            sorted((KOK / "ham").glob("*.json"))
            + sorted((KOK / "konsolide").glob("*.json"))
        )

    if not hedefler:
        print("HATA: işlenecek dosya bulunamadı")
        return 1

    hata = 0
    for yol in hedefler:
        if not yol.exists():
            print(f"YOK       {yol}")
            hata += 1
            continue
        try:
            durum, ok = isle(yol, args.check)
        except Exception as e:
            print(f"HATA      {yol.name}: {e}")
            hata += 1
            continue
        print(f"{durum:9s} {yol.relative_to(KOK)}")
        if not ok:
            hata += 1

    print(f"\n{len(hedefler)} dosya, {hata} sorun")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())