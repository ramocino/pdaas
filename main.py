"""
PDaaS API — Parametric Data as a Service
Otomatik servis keşfi: ham/ altındaki her JSON kendi meta bloğuyla
hangi bakanlığa ait olduğunu ve servis kodunu bildirir.
Meta eksikse dosya yolundan türetilir.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, List, Any
import json, time, uuid
from datetime import datetime, timezone

BUILD_VERSION = "v9_fixed_discovery_2026_10_13"
BUILD_TIMESTAMP = "2026-10-13T12:00:00Z"

app = FastAPI(
    title="PDaaS API",
    version="3.2.0",
    description="Parametric Data as a Service — Turkish public parameters (recursive auto-discovery)",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

KOK = Path(__file__).parent
HAM_KOK = KOK / "ham"
_METRICS = {"requests": 0, "total_ms": 0.0, "max_ms": 0.0}

_SERVIS_KATALOGU: Dict[tuple, dict] = {}


# ═══════════════════════════════════════════════════════════════
# STATİK DOSYA SUNUMU
# ═══════════════════════════════════════════════════════════════
if HAM_KOK.exists():
    app.mount("/ham", StaticFiles(directory=str(HAM_KOK)), name="ham")


# ═══════════════════════════════════════════════════════════════
# YARDIMCILAR
# ═══════════════════════════════════════════════════════════════
def _zaman_damgasi() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _metrik_kaydet(sure_ms: float):
    _METRICS["requests"] += 1
    _METRICS["total_ms"] += sure_ms
    if sure_ms > _METRICS["max_ms"]:
        _METRICS["max_ms"] = sure_ms


def _json_oku(yol: Path):
    try:
        return json.loads(yol.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _kayitlari_al(veri) -> list:
    if isinstance(veri, list):
        return veri
    if isinstance(veri, dict):
        if isinstance(veri.get("kayitlar"), list):
            return veri["kayitlar"]
        if isinstance(veri.get("data"), list):
            return veri["data"]
        for v in veri.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def _kayit_bul(kayitlar: list, alan_adlari: list, deger: str):
    hedef = str(deger).strip()
    for alan in alan_adlari:
        for k in kayitlar:
            if str(k.get(alan, "")).strip() == hedef:
                return k
    for alan in alan_adlari:
        for k in kayitlar:
            if str(k.get(alan, "")).strip().startswith(hedef):
                return k
    hedef_temiz = hedef.replace(".", "")
    for alan in alan_adlari:
        for k in kayitlar:
            if str(k.get(alan, "")).strip().replace(".", "").startswith(hedef_temiz):
                return k
    return None


# ═══════════════════════════════════════════════════════════════
# BAKANLIK ADI HARİTASI
# ═══════════════════════════════════════════════════════════════
_BAKANLIK_ADLARI = {
    "ticaret":  "T.C. Ticaret Bakanlığı",
    "tb":       "T.C. Ticaret Bakanlığı",
    "hvmb":     "T.C. Hazine ve Maliye Bakanlığı",
    "hazine":   "T.C. Hazine ve Maliye Bakanlığı",
    "csgb":     "T.C. Çalışma ve Sosyal Güvenlik Bakanlığı",
    "sgk":      "T.C. Sosyal Güvenlik Kurumu",
    "tuik":     "Türkiye İstatistik Kurumu",
    "csidb":    "T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı",
    "etkb":     "T.C. Enerji ve Tabii Kaynaklar Bakanlığı",
    "genel":    "Genel Referans Veriler",
}


# ═══════════════════════════════════════════════════════════════
# OTOMATİK KATALOG TARAMASI (Geliştirilmiş)
# ═══════════════════════════════════════════════════════════════
def _katalog_tara() -> dict:
    _SERVIS_KATALOGU.clear()
    if not HAM_KOK.exists():
        return _SERVIS_KATALOGU

    for f in sorted(HAM_KOK.rglob("*.json")):
        veri = _json_oku(f)
        if not isinstance(veri, dict):
            continue

        meta = veri.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}

        dosya_stem = f.stem.lower() # örn: gtip-kodlari, cpc-kodlari, nace-kodlari

        # Bakanlık tespiti (meta'dan veya dosya adına/servis koduna göre akıllı eşleme)
        bak = (meta.get("bakanlik") or "").strip().lower()
        if not bak or bak == "tb":
            if "gtip" in dosya_stem or "cpc" in dosya_stem or "ithalat" in dosya_stem:
                bak = "ticaret"
            elif "nace" in dosya_stem or "istatistik" in dosya_stem:
                bak = "tuik"
            elif "asgari" in dosya_stem or "sigorta" in dosya_stem or "isco" in dosya_stem:
                bak = "csgb"
            elif "vergi" in dosya_stem or "kdv" in dosya_stem or "otv" in dosya_stem:
                bak = "hvmb"
            else:
                bak = "ticaret"

        bakanlik_adi = (
            meta.get("bakanlik_adi")
            or _BAKANLIK_ADLARI.get(bak)
            or "T.C. Ticaret Bakanlığı"
        )

        svc = (meta.get("servis_kodu") or dosya_stem).strip().lower()
        servis_adi = meta.get("servis_adi") or dosya_stem.replace("-", " ").title()

        anahtar = (bak, svc)
        k = _SERVIS_KATALOGU.get(anahtar)
        if not k:
            k = {
                "bakanlik":              bak,
                "bakanlik_adi":          bakanlik_adi,
                "servis_kodu":           svc,
                "servis_adi":            servis_adi,
                "tip":                   (meta.get("tip") or "agac").lower(),
                "join":                  meta.get("join") or "kod",
                "surum":                 meta.get("surum") or meta.get("dosya_surumu") or "2026.01.01",
                "yayinci":               meta.get("yayinci"),
                "kaynak":                meta.get("kaynak"),
                "gecerlilik_baslangic":  meta.get("gecerlilik_baslangic"),
                "gecerlilik_bitis":      meta.get("gecerlilik_bitis"),
                "dosyalar":              [],
            }
            _SERVIS_KATALOGU[anahtar] = k

        k["dosyalar"].append({
            "yol":          f,
            "rel":          str(f.relative_to(KOK)),
            "dosya_adi":    f.name,
            "kayit_sayisi": len(_kayitlari_al(veri)),
        })

    return _SERVIS_KATALOGU


_katalog_tara()


def _ortak_meta(k: dict) -> dict:
    return {
        "bakanlik":             k["bakanlik"],
        "bakanlik_adi":         k["bakanlik_adi"],
        "servis_kodu":          k["servis_kodu"],
        "servis_adi":           k["servis_adi"],
        "surum":                k["surum"],
        "yayinci":              k["yayinci"],
        "kaynak":               k["kaynak"],
        "gecerlilik_baslangic": k["gecerlilik_baslangic"],
        "gecerlilik_bitis":     k["gecerlilik_bitis"],
    }


def _servis_bul(bakanlik: str, servis_kodu: str) -> dict:
    k = _SERVIS_KATALOGU.get((bakanlik.lower(), servis_kodu.lower()))
    if not k:
        _katalog_tara()
        k = _SERVIS_KATALOGU.get((bakanlik.lower(), servis_kodu.lower()))
    if not k:
        # Alternatif olarak sadece servis koduna göre arayalım
        for (b, s), kayit in _SERVIS_KATALOGU.items():
            if s == servis_kodu.lower():
                return kayit
        raise HTTPException(404, f"Servis bulunamadı: {bakanlik}/{servis_kodu}")
    return k


# ═══════════════════════════════════════════════════════════════
# ENDPOINT'LER
# ═══════════════════════════════════════════════════════════════
@app.get("/", include_in_schema=False)
def ana_sayfa():
    yol = KOK / "index.html"
    if not yol.exists():
        return {"service": "PDaaS API", "version": "3.2.0"}
    return FileResponse(yol, media_type="text/html")


@app.get("/health")
def health():
    return {"status": "healthy", "build": BUILD_VERSION}


@app.get("/api/v1/katalog")
def katalog_listesi():
    _katalog_tara()
    servisler = []
    for (bak, svc), k in sorted(_SERVIS_KATALOGU.items()):
        toplam = sum(d["kayit_sayisi"] for d in k["dosyalar"])
        servisler.append({
            "bakanlik":      bak,
            "bakanlik_adi":  k["bakanlik_adi"],
            "servis_kodu":   svc,
            "servis_adi":    k["servis_adi"],
            "tip":           k["tip"],
            "join":          k["join"],
            "surum":         k["surum"],
            "yayinci":       k["yayinci"],
            "kaynak":        k["kaynak"],
            "gecerlilik_baslangic": k["gecerlilik_baslangic"],
            "dosya_sayisi":  len(k["dosyalar"]),
            "kayit_sayisi":  toplam,
            "endpoint":      f"/api/v1/{bak}/{svc}",
        })
    return {
        "service":   "PDaaS - Auto Catalog",
        "timestamp": _zaman_damgasi(),
        "toplam":    len(servisler),
        "servisler": servisler,
    }


@app.get("/api/v1/{bakanlik}/{servis_kodu}")
def servis_ozet(bakanlik: str, servis_kodu: str):
    t0 = time.perf_counter()
    k = _servis_bul(bakanlik, servis_kodu)

    tum = []
    for d in k["dosyalar"]:
        v = _json_oku(d["yol"])
        if v:
            tum.extend(_kayitlari_al(v))
    
    _metrik_kaydet((time.perf_counter() - t0) * 1000)
    return {
        **_ortak_meta(k),
        "tip": k["tip"],
        "join": k["join"],
        "toplam": len(tum),
        "kayitlar": tum
    }
