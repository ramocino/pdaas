#!/usr/bin/env python3
"""PDaaS tek komut: doğrula + arşivle + katalog üret.

Ham ve kurallar dosyalarına DOKUNMAZ (hiyerarşik olanlar parçalanır).
Sadece surumler/ altındaki kopyalara checksum eklenerek yazılır.
"""
import argparse
import copy
import hashlib
import json
import sys
from importlib import import_module
from pathlib import Path

try:
    Draft202012Validator = import_module("jsonschema").Draft202012Validator
except ModuleNotFoundError:
    Draft202012Validator = None

KATMANLAR = ("ham", "kurallar", "konsolide")
META_SEMA_ADI = "pdaas-meta-2.0.0.json"
KATALOG_SEMA_ADI = "pdaas-katalog-2.0.0.json"

# ════════════════════════════════════════════════════════════════════
#  GÖMÜLÜ ŞEMALAR
# ════════════════════════════════════════════════════════════════════
META_SEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://pdaas.com.tr/api/v1/meta/schema/pdaas-meta-2.0.0.json",
    "title": "PDaaS meta bloğu (2.0.0)",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_surumu", "servis", "katman", "yapi", "surum", "guncelleme",
                 "yayin_durumu", "zaman", "yayinci", "kaynaklar", "mevzuat_ref"],
    "properties": {
        "schema_surumu": {"const": "2.0.0"},
        "servis": {
            "type": "object", "additionalProperties": False, "required": ["kod", "ad"],
            "properties": {"kod": {"$ref": "#/$defs/slug"}, "ad": {"$ref": "#/$defs/i18n"}},
        },
        "katman": {"enum": ["ham", "kurallar", "konsolide"]},
        "yapi": {
            "type": "object", "additionalProperties": False,
            "required": ["tip", "kod_sistemi", "kapsam"],
            "properties": {
                "tip": {"enum": ["liste", "agac", "kural-seti"]},
                "kod_sistemi": {"enum": ["gtip", "cpc", "nace", "isco", "sgk", "csgb",
                                          "gib", "hvmb", "tuik", "diger"]},
                "kapsam": {"type": "array", "minItems": 1, "uniqueItems": True,
                           "items": {"type": "string", "minLength": 1}},
            },
        },
        "surum": {"$ref": "#/$defs/takvim_surumu"},
        "guncelleme": {"$ref": "#/$defs/tarih"},
        "yayin_durumu": {"enum": ["taslak", "yayinda", "kullanimdan_kalkti"]},
        "zaman": {
            "type": "object", "additionalProperties": False,
            "required": ["bazli", "baslangic", "bitis"],
            "properties": {
                "bazli": {"type": "boolean"},
                "baslangic": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/tarih"}]},
                "bitis": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/tarih"}]},
            },
        },
        "yayinci": {
            "type": "object", "additionalProperties": False,
            "required": ["kod", "ad", "kurumlar"],
            "properties": {
                "kod": {"$ref": "#/$defs/slug"},
                "ad": {"$ref": "#/$defs/i18n"},
                "birim": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/i18n"}]},
                "kurumlar": {"type": "array", "minItems": 1, "uniqueItems": True,
                             "items": {"$ref": "#/$defs/slug"}},
            },
        },
        "kaynaklar": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False, "required": ["kod", "tur"],
                "properties": {
                    "kod": {"$ref": "#/$defs/slug"},
                    "tur": {"type": "string", "minLength": 1},
                    "ad": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/i18n"}]},
                    "kurum_kod": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/slug"}]},
                    "url": {"oneOf": [{"type": "null"}, {"type": "string", "pattern": "^https?://"}]},
                    "resmi_gazete": {"oneOf": [{"type": "null"}, {"type": "string"}]},
                    "erisim_tarihi": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/tarih"}]},
                },
            },
        },
        "mevzuat_ref": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False, "required": ["tur", "ad"],
                "properties": {
                    "tur": {"type": "string", "minLength": 1},
                    "ad": {"$ref": "#/$defs/i18n"},
                    "karar_sayisi": {"type": ["string", "null"]},
                    "madde": {"type": ["string", "null"]},
                    "resmi_gazete": {"type": ["string", "null"]},
                    "tarih": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/tarih"}]},
                },
            },
        },
        "checksum": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        "parca": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object", "additionalProperties": False,
                    "required": ["tur", "kod", "ana_dosya"],
                    "properties": {
                        "tur": {"type": "string"},
                        "kod": {"type": "string"},
                        "bolum_kod": {"type": ["string", "null"]},
                        "ana_dosya": {"type": "string"},
                    },
                },
            ],
        },
        "uretim": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object", "additionalProperties": False,
                    "required": ["ham_kaynaklar", "kural_seti", "uretim_zamani", "eslesme_ozeti"],
                    "properties": {
                        "ham_kaynaklar": {
                            "type": "array", "minItems": 1,
                            "items": {
                                "type": "object", "additionalProperties": False,
                                "required": ["servis_kod", "surum", "checksum"],
                                "properties": {
                                    "servis_kod": {"$ref": "#/$defs/slug"},
                                    "surum": {"$ref": "#/$defs/takvim_surumu"},
                                    "checksum": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                                },
                            },
                        },
                        "kural_seti": {
                            "type": "object", "additionalProperties": False,
                            "required": ["kod", "surum"],
                            "properties": {
                                "kod": {"$ref": "#/$defs/slug"},
                                "surum": {"$ref": "#/$defs/takvim_surumu"},
                            },
                        },
                        "uretim_zamani": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T"},
                        "eslesme_ozeti": {
                            "type": "object", "additionalProperties": False,
                            "properties": {
                                "toplam": {"type": "integer", "minimum": 0},
                                "eslesen": {"type": "integer", "minimum": 0},
                                "eslesmeyen": {"type": "integer", "minimum": 0},
                            },
                        },
                    },
                },
            ],
        },
    },
    "allOf": [
        {"if": {"properties": {"katman": {"const": "konsolide"}}, "required": ["katman"]},
         "then": {"properties": {"uretim": {"type": "object"}}}},
        {"if": {"properties": {"zaman": {"properties": {"bazli": {"const": True}}, "required": ["bazli"]}},
                "required": ["zaman"]},
         "then": {"properties": {"zaman": {"properties": {"baslangic": {"type": "string"}}}}}},
    ],
    "$defs": {
        "slug": {"type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"},
        "i18n": {
            "type": "object", "additionalProperties": False, "required": ["tr"],
            "properties": {"tr": {"type": "string", "minLength": 1}, "en": {"type": ["string", "null"]}},
        },
        "takvim_surumu": {"type": "string", "pattern": "^\\d{4}\\.\\d{2}\\.\\d{2}(\\.\\d+)?$"},
        "tarih": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
    },
}

KATALOG_SEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://pdaas.com.tr/api/v1/meta/schema/pdaas-katalog-2.0.0.json",
    "title": "PDaaS katalog (2.0.0)",
    "type": "object", "additionalProperties": False,
    "required": ["schema_surumu", "guncelleme", "servisler"],
    "properties": {
        "schema_surumu": {"const": "2.0.0"},
        "guncelleme": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "servisler": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["kod", "ad", "tip", "kod_sistemi", "katmanlar"],
                "properties": {
                    "kod": {"type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"},
                    "ad": {"$ref": "#/$defs/i18n"},
                    "tip": {"enum": ["liste", "agac", "kural-seti"]},
                    "kod_sistemi": {"type": "string"},
                    "katmanlar": {
                        "type": "object", "additionalProperties": False, "minProperties": 1,
                        "properties": {
                            "ham": {"$ref": "#/$defs/katman_kaydi"},
                            "kurallar": {"$ref": "#/$defs/katman_kaydi"},
                            "konsolide": {"$ref": "#/$defs/katman_kaydi"},
                        },
                    },
                },
            },
        },
    },
    "$defs": {
        "i18n": {
            "type": "object", "additionalProperties": False, "required": ["tr"],
            "properties": {"tr": {"type": "string"}, "en": {"type": ["string", "null"]}},
        },
        "katman_kaydi": {
            "type": "object", "additionalProperties": False,
            "required": ["son", "url", "surumler_url", "checksum"],
            "properties": {
                "son": {"type": "string", "pattern": "^\\d{4}\\.\\d{2}\\.\\d{2}(\\.\\d+)?$"},
                "url": {"type": "string", "pattern": "^/"},
                "surumler_url": {"type": "string", "pattern": "^/"},
                "checksum": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            },
        },
    },
}

# ════════════════════════════════════════════════════════════════════
#  Yardımcılar
# ════════════════════════════════════════════════════════════════════

def kanonik(veri):
    return json.dumps(veri, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")

def sha256(veri):
    return "sha256:" + hashlib.sha256(kanonik(veri)).hexdigest()

def icerik_verisi(doc, meta):
    tip = (meta.get("yapi") or {}).get("tip")
    if tip == "kural-seti":
        return {"gruplar": doc.get("gruplar", {}), "kurallar": doc.get("kurallar", [])}
    return doc.get("kayitlar", [])

def yukle(yol):
    with open(yol, encoding="utf-8") as f:
        return json.load(f)

def yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")

class Rapor:
    def __init__(self):
        self.hatalar = []
        self.uyarilar = []
        self.bilgi = []
    def hata(self, d, m): self.hatalar.append((d, m))
    def uyari(self, d, m): self.uyarilar.append((d, m))
    def ekle(self, m): self.bilgi.append(m)
    def yazdir(self):
        for m in self.bilgi: print(m)
        for d, m in self.uyarilar: print(f"[UYARI] {d}: {m}")
        for d, m in self.hatalar: print(f"[HATA]  {d}: {m}")
        print(f"\n{len(self.hatalar)} hata, {len(self.uyarilar)} uyarı")

def semalari_kur(kok, rapor):
    klasor = kok / "meta" / "schema"
    klasor.mkdir(parents=True, exist_ok=True)
    for ad, sema in ((META_SEMA_ADI, META_SEMA), (KATALOG_SEMA_ADI, KATALOG_SEMA)):
        yol = klasor / ad
        if not yol.exists():
            yaz(yol, sema)
            rapor.ekle(f"Şema yazıldı: {yol.relative_to(kok)}")
    return {"meta": Draft202012Validator(META_SEMA), "katalog": Draft202012Validator(KATALOG_SEMA)}

def dogrula_meta(meta, validator, ad, rapor):
    hatalar = sorted(validator.iter_errors(meta), key=lambda e: list(map(str, e.absolute_path)))
    for e in hatalar:
        yer = ".".join(map(str, e.absolute_path)) or "(kök)"
        rapor.hata(ad, f"meta.{yer}: {e.message}")
    return not hatalar

def dogrula_govde(doc, meta, ad, rapor):
    if ad.endswith("index.json"):
        if not isinstance(doc.get("fasillar"), list) and not isinstance(doc.get("parcalar"), list):
            rapor.hata(ad, "'fasillar' veya 'parcalar' dolu bir liste olmalı")
            return False
        return True

    tip = meta["yapi"]["tip"]
    if tip in ("liste", "agac"):
        kayitlar = doc.get("kayitlar")
        if not isinstance(kayitlar, list) or not kayitlar:
            rapor.hata(ad, "'kayitlar' dolu bir liste olmalı")
            return False
        kodlar = set()
        for i, k in enumerate(kayitlar):
            if not isinstance(k, dict):
                rapor.hata(ad, f"kayıt #{i}: nesne olmalı"); continue
            kod = k.get("kod")
            if not isinstance(kod, str) or not kod:
                rapor.hata(ad, f"kayıt #{i}: 'kod' boş olmayan string olmalı"); continue
            if kod in kodlar:
                rapor.hata(ad, f"yinelenen kod: {kod}")
            kodlar.add(kod)
        return True
    if tip == "kural-seti":
        if not isinstance(doc.get("gruplar"), dict) or not doc["gruplar"]:
            rapor.hata(ad, "'gruplar' dolu bir nesne olmalı"); return False
        if not isinstance(doc.get("kurallar"), list) or not doc["kurallar"]:
            rapor.hata(ad, "'kurallar' dolu bir liste olmalı"); return False
        return True
    rapor.hata(ad, f"bilinmeyen yapi.tip: {tip!r}")
    return False

# ════════════════════════════════════════════════════════════════════
#  Hiyerarşik Verileri Parçalama
# ════════════════════════════════════════════════════════════════════
def hiyerarsi_parcala(kok, rapor):
    ayarlar = {
        "gtip-kodlari": {"seviye": 2, "klasor": "fasil"},
        "nace-kodlari": {"seviye": 1, "klasor": "bolum"},
        "cpc-kodlari":  {"seviye": 1, "klasor": "bolum"},
        "isco-kodlari": {"seviye": 1, "klasor": "bolum"},
    }
    for servis, ayar in ayarlar.items():
        kaynak = kok / "ham" / f"{servis}.json"
        if not kaynak.exists():
            continue
        try:
            doc = yukle(kaynak)
        except Exception as e:
            rapor.hata(f"ham/{servis}.json", f"okunamadı: {e}")
            continue
        meta = doc.get("meta", {})
        kayitlar = doc.get("kayitlar", [])

        # Ağaç yapısını kur (kod -> kayıt ve üst_kod -> çocuk kodlar)
        by_kod = {k["kod"]: k for k in kayitlar if isinstance(k, dict) and "kod" in k}
        cocuklar = {}
        for k in kayitlar:
            if not isinstance(k, dict) or "kod" not in k:
                continue
            ust = k.get("ust_kod")
            if ust:
                cocuklar.setdefault(ust, []).append(k["kod"])

        def torunlari_topla(kok_kod):
            sonuc = []
            stack = list(cocuklar.get(kok_kod, []))
            while stack:
                mevcut = stack.pop()
                if mevcut in by_kod:
                    sonuc.append(by_kod[mevcut])
                stack.extend(cocuklar.get(mevcut, []))
            return sonuc

        # Belirtilen seviyedeki kökleri bul
        kokler = [k for k in kayitlar if isinstance(k, dict) and k.get("seviye") == ayar["seviye"]]
        if not kokler:
            continue

        hedef_klasor = kok / "ham" / servis
        alt_klasor = hedef_klasor / ayar["klasor"]
        alt_klasor.mkdir(parents=True, exist_ok=True)

        for kok_k in kokler:
            kod = kok_k["kod"]
            parca_kayitlar = [kok_k] + torunlari_topla(kod)

            parca_meta = copy.deepcopy(meta)
            parca_meta["parca"] = {
                "tur": ayar["klasor"],
                "kod": kod,
                "bolum_kod": kok_k.get("ust_kod"),
                "ana_dosya": f"{servis}.json",
            }
            parca_doc = {"meta": parca_meta, "kayitlar": parca_kayitlar}
            yaz(alt_klasor / f"{kod}.json", parca_doc)

        # index.json
        index_meta = copy.deepcopy(meta)
        index_meta["parca"] = {
            "tur": "index",
            "kod": "index",
            "bolum_kod": None,
            "ana_dosya": f"{servis}.json",
        }
        index_doc = {
            "meta": index_meta,
            "parcalar": [
                {
                    "kod": k["kod"],
                    "ad_tr": k.get("tanim_tr") or k.get("ad_tr"),
                    "ad_en": k.get("tanim_en") or k.get("ad_en"),
                    "bolum_kod": k.get("ust_kod"),
                    "dosya": f"{ayar['klasor']}/{k['kod']}.json",
                }
                for k in kokler
            ],
        }
        yaz(hedef_klasor / "index.json", index_doc)
        rapor.ekle(f"{servis} {len(kokler)} parçaya ayrıldı ({ayar['klasor']} bazında)")

# ════════════════════════════════════════════════════════════════════
#  Analiz
# ════════════════════════════════════════════════════════════════════
def analiz(kok, katman, kaynak, semalar, rapor, force):
    ad = str(kaynak.relative_to(kok))
    try:
        doc = yukle(kaynak)
    except json.JSONDecodeError as e:
        rapor.hata(ad, f"geçersiz JSON: {e.msg} (satır {e.lineno})")
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict):
        rapor.hata(ad, "kök 'meta' nesnesi yok")
        return None
    meta = doc["meta"]
    yeni_hash = sha256(icerik_verisi(doc, meta))

    if "checksum" in meta and meta["checksum"] != yeni_hash:
        rapor.uyari(ad, f"ham dosyadaki checksum güncel değil; arşive güncel hash yazılacak")

    arsiv_doc = copy.deepcopy(doc)
    arsiv_doc["meta"]["checksum"] = yeni_hash

    if not dogrula_meta(arsiv_doc["meta"], semalar["meta"], ad, rapor):
        return None
    if meta["katman"] != katman:
        rapor.hata(ad, f"meta.katman {meta['katman']!r} ile klasör {katman!r} uyuşmuyor")
        return None

    # Dosya adı kontrolü (parça veya index değilse)
    if "parca" not in meta and kaynak.name != "index.json":
        if meta["servis"]["kod"] != kaynak.stem:
            rapor.hata(ad, f"meta.servis.kod {meta['servis']['kod']!r} ≠ dosya adı {kaynak.stem!r}")
            return None

    if not dogrula_govde(doc, meta, ad, rapor):
        return None

    surum = meta["surum"]
    arsiv_durum = "yeni"

    if "parca" in meta:
        # Parça arşivleme: surumler/<servis>/<surum>/<relative_path>
        ana_kod = meta["servis"]["kod"]
        arsiv_klasoru = kok / katman / "surumler" / ana_kod / surum
        try:
            rel_yol = kaynak.relative_to(kok / katman / ana_kod)
            arsiv = arsiv_klasoru / rel_yol
        except ValueError:
            rapor.hata(ad, f"parça yolu hesaplanamadı")
            return None
    elif kaynak.name == "index.json":
        # Konsolide index.json ana dosyadır: surumler/<servis>/<surum>.json
        arsiv = kok / katman / "surumler" / meta["servis"]["kod"] / f"{surum}.json"
    else:
        arsiv = kok / katman / "surumler" / kaynak.stem / f"{surum}.json"

    if arsiv.exists():
        try:
            eski = yukle(arsiv)
            eski_hash = sha256(icerik_verisi(eski, eski.get("meta", {})))
        except (json.JSONDecodeError, KeyError):
            rapor.hata(str(arsiv.relative_to(kok)), "bozuk arşiv dosyası")
            return None
        if eski_hash == yeni_hash:
            arsiv_durum = "ayni"
        elif force:
            arsiv_durum = "ezilecek"
            rapor.uyari(ad, f"arşivdeki {surum} farklı içerikle var; --force ile ezilecek")
        else:
            rapor.hata(ad, f"arşivde {surum} farklı içerikle var; sürümü artırın ya da --force")
            return None

    return {"yol": kaynak, "ad": ad, "arsiv_doc": arsiv_doc, "meta": meta,
            "hash": yeni_hash, "arsiv": arsiv, "arsiv_durum": arsiv_durum}

def katalog_uret(bilgiler):
    servisler = {}
    for b in bilgiler:
        m = b["meta"]
        # Parça dosyalarını kataloğa ekleme (ana dosya zaten var)
        if "parca" in m:
            continue
        kod = m["servis"]["kod"]
        s = servisler.setdefault(kod, {
            "kod": kod, "ad": m["servis"]["ad"],
            "tip": m["yapi"]["tip"], "kod_sistemi": m["yapi"]["kod_sistemi"],
            "katmanlar": {},
        })
        s["katmanlar"][m["katman"]] = {
            "son": m["surum"],
            "url": f"/{m['katman']}/{kod}.json",
            "surumler_url": f"/{m['katman']}/surumler/{kod}/",
            "checksum": b["hash"],
        }
    return {
        "schema_surumu": "2.0.0",
        "guncelleme": max(b["meta"]["guncelleme"] for b in bilgiler),
        "servisler": sorted(servisler.values(), key=lambda s: s["kod"]),
    }

# ════════════════════════════════════════════════════════════════════
#  Ana akış
# ════════════════════════════════════════════════════════════════════
def ana():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default=None)
    ap.add_argument("--sadece-dogrula", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if Draft202012Validator is None:
        print("Eksik: pip install jsonschema", file=sys.stderr)
        return 1

    kok = Path(args.kok).expanduser().resolve() if args.kok \
          else Path(__file__).resolve().parent.parent
    print(f"Kök: {kok}")
    print(f"Mod: {'SADECE DOĞRULA' if args.sadece_dogrula else 'TAM'}\n")

    rapor = Rapor()
    semalar = semalari_kur(kok, rapor)

    # ── Hiyerarşik dosyaları parçala ──
    if not args.sadece_dogrula:
        hiyerarsi_parcala(kok, rapor)

    bilgiler = []
    for katman in KATMANLAR:
        klasor = kok / katman
        if not klasor.is_dir():
            continue
        # Alt klasörlerdeki json'ları da tara (surumler hariç)
        for kaynak in sorted(klasor.rglob("*.json")):
            if "surumler" in kaynak.parts:
                continue
            b = analiz(kok, katman, kaynak, semalar, rapor, args.force)
            if b:
                bilgiler.append(b)

    if rapor.hatalar:
        rapor.yazdir()
        print("\nDosya yazılmadı: önce yukarıdaki hataları düzeltin.")
        return 1

    if args.sadece_dogrula:
        for b in bilgiler:
            rapor.ekle(f"OK {b['ad']} → {b['meta']['surum']}")
        rapor.yazdir()
        return 0

    arsivlenen = 0
    for b in bilgiler:
        if b["arsiv_durum"] in ("yeni", "ezilecek"):
            yaz(b["arsiv"], b["arsiv_doc"])
            arsivlenen += 1

    if bilgiler:
        ana_bilgiler = [b for b in bilgiler if "parca" not in b["meta"]]
        if ana_bilgiler:
            kat = katalog_uret(ana_bilgiler)
            kat_validator = semalar["katalog"]
            hatalar = list(kat_validator.iter_errors(kat))
            if hatalar:
                for e in hatalar:
                    rapor.hata("katalog.json", f"{'.'.join(map(str, e.absolute_path)) or '(kök)'}: {e.message}")
            else:
                yaz(kok / "katalog.json", kat)
                rapor.ekle(f"katalog.json yazıldı ({len(kat['servisler'])} servis)")

    rapor.ekle(f"{len(bilgiler)} dosya tarandı, {arsivlenen} arşiv kopyası oluşturuldu")
    rapor.yazdir()
    return 1 if rapor.hatalar else 0

if __name__ == "__main__":
    sys.exit(ana())