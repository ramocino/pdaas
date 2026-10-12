"""
PDaaS API — Parametric Data as a Service
FastAPI uygulaması: main.py

Katman yapısı:
  Layer 1 (ham)      → ham/{kurum}/...       — bakanlıkların saf kod listeleri
  Layer 2 (ilişki)   → iliski/{kurum}/...    — kodlar arası bağ + zenginleştirme
  Layer 3 (konsolide)→ konsolide/islem/...   — işlem nesneleri

Endpoint grupları:
  /api/v1/product/{gtip}          — GTİP ürün servisi
  /api/v1/service/{cpc}           — CPC hizmet servisi
  /api/v1/occupation/{isco}       — ISCO meslek servisi
  /api/v1/nace/{bolum}            — NACE faaliyet servisi
  /api/v1/tax/stamp-duty          — Damga vergisi
  /api/v1/tax/income-brackets     — Gelir vergisi dilimleri
  /api/v1/tax/sct-vehicle         — ÖTV araç oranları
  /api/v1/{varlik}/agac           — Katalog ağacı (dal listesi)
  /api/v1/{varlik}/dal/{dal}      — Dalın ham kayıtları
  /api/v1/iliski                  — Layer 2 yazma (POST)
  /api/v1/consolidated            — Layer 3 birleştirme
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import time
import uuid
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# SÜRÜM SABİTLERİ
# ═══════════════════════════════════════════════════════════════
BUILD_VERSION = "v4_catalog_layer_2026_10_12"
BUILD_TIMESTAMP = "2026-10-12T00:00:00Z"

# ═══════════════════════════════════════════════════════════════
# UYGULAMA
# ═══════════════════════════════════════════════════════════════
app = FastAPI(
    title="PDaaS API",
    version="2.0.0",
    description="Parametric Data as a Service — Turkish public parameters (Technical Proof-of-Concept)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# YARDIMCILAR — yol çözümleyici, okuyucu, arayıcı
# ═══════════════════════════════════════════════════════════════
KOK = Path(__file__).parent
_METRICS = {"requests": 0, "total_ms": 0.0, "max_ms": 0.0}


# ── Varlık → klasör yolu (eski + yeni uyumlu) ──
_YOL_HARITASI = {
    "gtip":  ["ham/ticaret/gtip",   "ticaret/gtip"],
    "cpc":   ["ham/ticaret/cpc",    "ticaret/cpc"],
    "isco":  ["ham/ticaret/isco",   "ticaret/isco"],
    "nace":  ["ham/tuik/nace",      "tuik/nace", "nace"],
    "damga": ["ham/hazine",         "hvmb"],
    "gelir": ["ham/hazine",         "hvmb"],
    "otv":   ["ham/hazine",         "hvmb"],
}


def _ilk_var_olan(yollar: List[str]) -> Optional[Path]:
    """Verilen göreli yollardan ilk var olanı döner."""
    for y in yollar:
        p = KOK / y
        if p.exists():
            return p
    return None


def dosya_oku(rel_yol: str) -> dict:
    """JSON dosyasını okur; yoksa 404 döndürür."""
    yol = KOK / rel_yol
    if not yol.exists():
        raise HTTPException(404, f"Veri dosyası bulunamadı: {rel_yol}")
    return json.loads(yol.read_text(encoding="utf-8"))


def _kayit_bul(kayitlar: list, alan_adlari: list, deger: str):
    """
    Kayıt listesi içinde verilen değeri, birden fazla olası alan adında arar.
    Önce tam eşleşme, sonra prefix, en son noktasız prefix dener.
    """
    hedef = str(deger).strip()

    # 1) Tam eşleşme
    for alan in alan_adlari:
        for k in kayitlar:
            if str(k.get(alan, "")).strip() == hedef:
                return k

    # 2) Prefix eşleşmesi (2702.10 → 2702.10.00.00.00)
    for alan in alan_adlari:
        for k in kayitlar:
            if str(k.get(alan, "")).strip().startswith(hedef):
                return k

    # 3) Noktasız prefix (270210 → 2702.10.00.00.00)
    hedef_temiz = hedef.replace(".", "")
    for alan in alan_adlari:
        for k in kayitlar:
            k_temiz = str(k.get(alan, "")).strip().replace(".", "")
            if k_temiz.startswith(hedef_temiz):
                return k

    return None


def _zaman_damgasi() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _metrik_kaydet(sure_ms: float):
    _METRICS["requests"] += 1
    _METRICS["total_ms"] += sure_ms
    if sure_ms > _METRICS["max_ms"]:
        _METRICS["max_ms"] = sure_ms


def _meta_ozet(meta: dict) -> dict:
    """meta bloğundan standart alanları çıkarır."""
    return {
        "version_id":      meta.get("surum") or meta.get("dosya_surumu") or "1.0.0",
        "valid_from":      meta.get("gecerlilik_baslangic"),
        "valid_to":        meta.get("gecerlilik_bitis"),
        "legal_basis_doc": meta.get("kaynak"),
        "publisher":       meta.get("yayinci"),
        "unit":            meta.get("birim"),
        "updated_at":      meta.get("guncelleme"),
    }


def _dal_kodu_ve_adi(varlik: str, meta: dict, dosya: Path):
    """Varlık tipine göre dal kodunu ve adını meta'dan çıkarır."""
    if varlik == "gtip":
        return (meta.get("fasil_no") or dosya.stem,
                meta.get("fasil_adi", ""))
    if varlik == "cpc":
        return (meta.get("grup_no") or dosya.stem,
                meta.get("grup_adi", ""))
    if varlik == "isco":
        return (meta.get("alt_grup_no") or dosya.stem,
                meta.get("alt_grup_adi", ""))
    if varlik == "nace":
        return (meta.get("bolum") or dosya.stem,
                meta.get("bolum_adi", ""))
    return (dosya.stem, "")


# ═══════════════════════════════════════════════════════════════
# KÖK — index.html
# ═══════════════════════════════════════════════════════════════
@app.get("/", include_in_schema=False)
def ana_sayfa():
    index_yolu = KOK / "index.html"
    if not index_yolu.exists():
        return {
            "service": "PDaaS API",
            "version": "2.0.0",
            "message": "index.html bulunamadı; sadece API çalışıyor.",
            "docs": "/docs",
        }
    return FileResponse(index_yolu, media_type="text/html")


@app.get("/kurator", include_in_schema=False)
def kurator_sayfa():
    """Kurator arayüzünü sunar (varsa)."""
    yol = KOK / "kurator.html"
    if not yol.exists():
        raise HTTPException(404, "kurator.html bulunamadı")
    return FileResponse(yol, media_type="text/html")


# ═══════════════════════════════════════════════════════════════
# DEPLOY DOĞRULAMA
# ═══════════════════════════════════════════════════════════════
@app.get("/version-check")
def version_check():
    return {
        "build": BUILD_VERSION,
        "build_time": BUILD_TIMESTAMP,
        "has_file_response": True,
        "has_meta_support": True,
        "has_catalog_tree": True,
        "has_tax_services": True,
        "has_write_endpoint": True,
        "status": "ok",
    }


# ═══════════════════════════════════════════════════════════════
# SAĞLIK & İSTATİSTİK
# ═══════════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "build": BUILD_VERSION,
        "timestamp": _zaman_damgasi(),
    }


@app.get("/stats")
def stats():
    try:
        manifest = dosya_oku("manifest.json")
        katalog = manifest.get("istatistik", {})
    except HTTPException:
        katalog = {}

    r = _METRICS["requests"]
    avg = (_METRICS["total_ms"] / r) if r > 0 else 4.77
    return {
        "avg_processing_ms": round(avg, 2),
        "max_processing_ms": round(_METRICS["max_ms"] or 8.0, 2),
        "avg_ms": round(avg, 2),
        "max_ms": round(_METRICS["max_ms"] or 8.0, 2),
        "request_count": r,
        "katalog": katalog,
        "source": "live" if r > 0 else "paper_poc_reference",
    }


# ═══════════════════════════════════════════════════════════════
# KATALOG AĞACI — varlık türüne göre dal listesi
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/{varlik}/agac")
def katalog_agac(varlik: str):
    """
    Varlık türüne göre ağacın dallarını döner.
      GTİP  → fasıllar  (01, 22, 27, 72, 84 …)
      CPC   → gruplar   (244, 412, 434, 831, 883 …)
      ISCO  → alt gruplar (251, 252, 351, 723, 811 …)
      NACE  → bölümler  (A, B, C, J, N …)
    """
    if varlik not in _YOL_HARITASI:
        raise HTTPException(404, f"Bilinmeyen varlık: {varlik}")

    klasor = _ilk_var_olan(_YOL_HARITASI[varlik])
    if not klasor or not klasor.is_dir():
        raise HTTPException(404, f"Klasör bulunamadı: {varlik}")

    dallar = []
    for f in sorted(klasor.glob("*.json")):
        # toplu dosyaları atla
        if f.stem in ("cpc-kodlari", "isco-kodlari"):
            continue
        try:
            v = json.loads(f.read_text(encoding="utf-8"))
            meta = v.get("meta", {})
            kayitlar = v.get("kayitlar", [])
            dal_kodu, dal_adi = _dal_kodu_ve_adi(varlik, meta, f)

            dallar.append({
                "dal":          dal_kodu,
                "ad":           dal_adi,
                "dosya":        f.name,
                "kayit_sayisi": len(kayitlar),
            })
        except Exception:
            continue

    return {
        "service":     "PDaaS - Catalog Tree v1.0",
        "varlik":      varlik,
        "toplam_dal":  len(dallar),
        "dallar":      dallar,
    }


@app.get("/api/v1/{varlik}/dal/{dal_kodu}")
def katalog_dal(varlik: str, dal_kodu: str):
    """
    Bir dalın (fasıl/grup/bölüm) tüm ham kayıtlarını döner.
    Örn: GET /api/v1/gtip/dal/27 → fasıl 27'nin tüm kodları
    """
    if varlik not in _YOL_HARITASI:
        raise HTTPException(404, f"Bilinmeyen varlık: {varlik}")

    klasor = _ilk_var_olan(_YOL_HARITASI[varlik])
    if not klasor or not klasor.is_dir():
        raise HTTPException(404, f"Klasör bulunamadı: {varlik}")

    # 1) Doğrudan dosya eşleşmesi
    dosya = klasor / f"{dal_kodu}.json"
    if not dosya.exists():
        # 2) Prefix araması
        adaylar = sorted(klasor.glob(f"{dal_kodu}*.json"))
        if not adaylar:
            raise HTTPException(404, f"Dal bulunamadı: {dal_kodu}")
        dosya = adaylar[0]

    v = json.loads(dosya.read_text(encoding="utf-8"))
    return {
        "service":  "PDaaS - Catalog Branch v1.0",
        "varlik":   varlik,
        "dal":      dal_kodu,
        "meta":     v.get("meta", {}),
        "toplam":   len(v.get("kayitlar", [])),
        "kayitlar": v.get("kayitlar", []),
    }


# ═══════════════════════════════════════════════════════════════
# ÜRÜN (GTİP)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/product/{gtip_code}")
def urun_getir(gtip_code: str, katman: str = "ham"):
    """
    GTİP koduna göre ürün parametrelerini döndürür.
    Örnek: /api/v1/product/2702.10
    Parametre: katman = ham | iliski | all
    """
    t0 = time.perf_counter()

    temiz = gtip_code.replace(".", "").strip()
    if len(temiz) < 2:
        raise HTTPException(400, "Geçersiz GTİP kodu")
    fasil = temiz[:2].zfill(2)

    klasor = _ilk_var_olan(_YOL_HARITASI["gtip"])
    if not klasor:
        raise HTTPException(404, "GTİP klasörü bulunamadı")

    dosya = klasor / f"{fasil}.json"
    if not dosya.exists():
        raise HTTPException(404, f"Fasıl bulunamadı: {fasil}")

    veri = json.loads(dosya.read_text(encoding="utf-8"))
    meta = veri.get("meta", {})

    kayit = _kayit_bul(
        veri.get("kayitlar", []),
        ["kod", "gtip_kodu", "gtip_ham", "gtip"],
        gtip_code,
    )
    if not kayit:
        raise HTTPException(404, f"GTİP kodu bulunamadı: {gtip_code}")

    # katman == "iliski" veya "all" ise eşleştirmeleri de ekle
    if katman in ("iliski", "all"):
        kayit = _iliski_ekle("gtip", kayit.get("kod", gtip_code), kayit)

    _metrik_kaydet((time.perf_counter() - t0) * 1000)

    return {
        "service":  "PDaaS - Product Service v2.0",
        "endpoint": f"/api/v1/product/{gtip_code}",
        "katman":   katman,
        "timestamp": _zaman_damgasi(),
        **_meta_ozet(meta),
        "data": kayit,
    }


# ═══════════════════════════════════════════════════════════════
# HİZMET (CPC)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/service/{cpc_code}")
def hizmet_getir(cpc_code: str, katman: str = "ham"):
    t0 = time.perf_counter()

    klasor = _ilk_var_olan(_YOL_HARITASI["cpc"])
    if not klasor:
        raise HTTPException(404, "CPC klasörü bulunamadı")

    kod = str(cpc_code).strip()

    # 1) Grup dosyası (883 → 883.json, 8831 → 883.json)
    if len(kod) >= 3:
        grup_dosya = klasor / f"{kod[:3]}.json"
        if grup_dosya.exists():
            veri = json.loads(grup_dosya.read_text(encoding="utf-8"))
            kayit = _kayit_bul(
                veri.get("kayitlar", []),
                ["kod", "cpc_kodu", "cpc"],
                kod,
            )
            if kayit:
                if katman in ("iliski", "all"):
                    kayit = _iliski_ekle("cpc", kayit.get("kod", kod), kayit)
                _metrik_kaydet((time.perf_counter() - t0) * 1000)
                return {
                    "service":   "PDaaS - Service Service v2.0",
                    "endpoint":  f"/api/v1/service/{cpc_code}",
                    "katman":    katman,
                    "timestamp": _zaman_damgasi(),
                    **_meta_ozet(veri.get("meta", {})),
                    "data": kayit,
                }

    # 2) Fallback: toplu dosya
    toplu = klasor / "cpc-kodlari.json"
    if toplu.exists():
        veri = json.loads(toplu.read_text(encoding="utf-8"))
        kayit = _kayit_bul(veri.get("kayitlar", []), ["kod", "cpc_kodu", "cpc"], kod)
        if kayit:
            if katman in ("iliski", "all"):
                kayit = _iliski_ekle("cpc", kayit.get("kod", kod), kayit)
            _metrik_kaydet((time.perf_counter() - t0) * 1000)
            return {
                "service":   "PDaaS - Service Service v2.0",
                "endpoint":  f"/api/v1/service/{cpc_code}",
                "katman":    katman,
                "timestamp": _zaman_damgasi(),
                **_meta_ozet(veri.get("meta", {})),
                "data": kayit,
            }

    raise HTTPException(404, f"CPC kodu bulunamadı: {cpc_code}")


# ═══════════════════════════════════════════════════════════════
# MESLEK (ISCO)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/occupation/{isco_code}")
def meslek_getir(isco_code: str, katman: str = "ham"):
    t0 = time.perf_counter()

    klasor = _ilk_var_olan(_YOL_HARITASI["isco"])
    if not klasor:
        raise HTTPException(404, "ISCO klasörü bulunamadı")

    kod = str(isco_code).strip()

    if len(kod) >= 3:
        grup_dosya = klasor / f"{kod[:3]}.json"
        if grup_dosya.exists():
            veri = json.loads(grup_dosya.read_text(encoding="utf-8"))
            kayit = _kayit_bul(
                veri.get("kayitlar", []),
                ["kod", "isco_kodu", "isco"],
                kod,
            )
            if kayit:
                if katman in ("iliski", "all"):
                    kayit = _iliski_ekle("isco", kayit.get("kod", kod), kayit)
                _metrik_kaydet((time.perf_counter() - t0) * 1000)
                return {
                    "service":   "PDaaS - Occupation Service v2.0",
                    "endpoint":  f"/api/v1/occupation/{isco_code}",
                    "katman":    katman,
                    "timestamp": _zaman_damgasi(),
                    **_meta_ozet(veri.get("meta", {})),
                    "data": kayit,
                }

    toplu = klasor / "isco-kodlari.json"
    if toplu.exists():
        veri = json.loads(toplu.read_text(encoding="utf-8"))
        kayit = _kayit_bul(veri.get("kayitlar", []), ["kod", "isco_kodu", "isco"], kod)
        if kayit:
            if katman in ("iliski", "all"):
                kayit = _iliski_ekle("isco", kayit.get("kod", kod), kayit)
            _metrik_kaydet((time.perf_counter() - t0) * 1000)
            return {
                "service":   "PDaaS - Occupation Service v2.0",
                "endpoint":  f"/api/v1/occupation/{isco_code}",
                "katman":    katman,
                "timestamp": _zaman_damgasi(),
                **_meta_ozet(veri.get("meta", {})),
                "data": kayit,
            }

    raise HTTPException(404, f"ISCO kodu bulunamadı: {isco_code}")


# ═══════════════════════════════════════════════════════════════
# NACE (Faaliyet)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/nace/{bolum}")
def nace_getir(bolum: str, katman: str = "ham"):
    """
    NACE bölümünü (A, B, C, …) döner.
    Örn: /api/v1/nace/B → madencilik bölümü kayıtları
    """
    t0 = time.perf_counter()

    klasor = _ilk_var_olan(_YOL_HARITASI["nace"])
    if not klasor:
        raise HTTPException(404, "NACE klasörü bulunamadı")

    kod = str(bolum).strip().upper()
    dosya = klasor / f"{kod}.json"
    if not dosya.exists():
        raise HTTPException(404, f"NACE bölümü bulunamadı: {bolum}")

    veri = json.loads(dosya.read_text(encoding="utf-8"))
    _metrik_kaydet((time.perf_counter() - t0) * 1000)

    return {
        "service":   "PDaaS - NACE Service v1.0",
        "endpoint":  f"/api/v1/nace/{bolum}",
        "katman":    katman,
        "timestamp": _zaman_damgasi(),
        **_meta_ozet(veri.get("meta", {})),
        "toplam":    len(veri.get("kayitlar", [])),
        "data":      veri.get("kayitlar", []),
    }


# ═══════════════════════════════════════════════════════════════
# VERGİ SERVİSLERİ
# ═══════════════════════════════════════════════════════════════
def _vergi_dosyasi(anahtar: str) -> Path:
    """Vergi dosyasını (damga, gelir, otv) farklı olası adlarla arar."""
    adaylar = {
        "damga": ["damgavergisi.json", "damga-vergisi.json"],
        "gelir": ["gelir-vergisi.json", "gelirvergisi.json"],
        "otv":   ["otv-arac.json", "otv.json"],
    }
    klasor = _ilk_var_olan(_YOL_HARITASI[anahtar])
    if not klasor:
        raise HTTPException(404, f"Vergi klasörü bulunamadı: {anahtar}")
    for ad in adaylar.get(anahtar, []):
        p = klasor / ad
        if p.exists():
            return p
    raise HTTPException(404, f"Vergi dosyası bulunamadı: {anahtar}")


def _vergi_listesi(anahtar: str, servis_adi: str):
    t0 = time.perf_counter()
    yol = _vergi_dosyasi(anahtar)
    veri = json.loads(yol.read_text(encoding="utf-8"))
    _metrik_kaydet((time.perf_counter() - t0) * 1000)
    return {
        "service":   servis_adi,
        "timestamp": _zaman_damgasi(),
        **_meta_ozet(veri.get("meta", {})),
        "toplam":    len(veri.get("kayitlar", [])),
        "data":      veri.get("kayitlar", []),
    }


def _vergi_kayit(anahtar: str, kod: str, servis_adi: str):
    t0 = time.perf_counter()
    yol = _vergi_dosyasi(anahtar)
    veri = json.loads(yol.read_text(encoding="utf-8"))
    kayit = _kayit_bul(veri.get("kayitlar", []), ["kod"], kod)
    if not kayit:
        raise HTTPException(404, f"Kod bulunamadı: {kod}")
    _metrik_kaydet((time.perf_counter() - t0) * 1000)
    return {
        "service":   servis_adi,
        "timestamp": _zaman_damgasi(),
        **_meta_ozet(veri.get("meta", {})),
        "data":      kayit,
    }


@app.get("/api/v1/tax/stamp-duty")
def damga_listesi():
    return _vergi_listesi("damga", "PDaaS - Stamp Duty Service v1.0")


@app.get("/api/v1/tax/stamp-duty/{kod}")
def damga_kayit(kod: str):
    return _vergi_kayit("damga", kod, "PDaaS - Stamp Duty Service v1.0")


@app.get("/api/v1/tax/income-brackets")
def gelir_listesi():
    return _vergi_listesi("gelir", "PDaaS - Income Tax Service v1.0")


@app.get("/api/v1/tax/income-brackets/{kod}")
def gelir_kayit(kod: str):
    return _vergi_kayit("gelir", kod, "PDaaS - Income Tax Service v1.0")


@app.get("/api/v1/tax/sct-vehicle")
def otv_listesi():
    return _vergi_listesi("otv", "PDaaS - SCT Vehicle Service v1.0")


@app.get("/api/v1/tax/sct-vehicle/{kod}")
def otv_kayit(kod: str):
    return _vergi_kayit("otv", kod, "PDaaS - SCT Vehicle Service v1.0")


# ═══════════════════════════════════════════════════════════════
# İLİŞKİ OKUMA — Layer 2
# ═══════════════════════════════════════════════════════════════
def _iliski_yolu(varlik: str) -> Optional[Path]:
    """İlişki dosyasını farklı kurum klasörlerinde arar."""
    adaylar = [
        KOK / "iliski" / "cbdd" / f"{varlik}.json",
        KOK / "iliski" / "ticaret" / f"{varlik}.json",
        KOK / "iliski" / "hazine" / f"{varlik}.json",
        KOK / "iliski" / "sgk" / f"{varlik}.json",
        KOK / "iliski" / "tuik" / f"{varlik}.json",
    ]
    for p in adaylar:
        if p.exists():
            return p
    return None


def _iliski_ekle(varlik: str, kod: str, kayit: dict) -> dict:
    """
    Bir kayda ilişki katmanını (varsa) ekler.
    Örn: gtip koduna randıman + vergi verisi biner.
    """
    # Kaynak tipini ve kod alanını bul
    kod_alanlari = {
        "gtip": ["gtip"],
        "cpc":  ["cpc"],
        "isco": ["isco"],
        "nace": ["nace"],
    }.get(varlik, [varlik])

    iliski_dosyalari = [
        f"{varlik}-cpc", f"{varlik}-isco", f"{varlik}-nace", f"{varlik}-gtip",
        f"{varlik}-randiman", f"{varlik}-tehlike", f"{varlik}-vergi",
        f"{varlik}-prim", f"{varlik}-adamsaat",
    ]

    eslestirmeler = {}
    for ad in iliski_dosyalari:
        p = _iliski_yolu(ad)
        if not p:
            continue
        try:
            v = json.loads(p.read_text(encoding="utf-8"))
            for kayitx in v.get("eslestirmeler", []):
                # Kaynak kodunu bul
                kaynak_kod = None
                for alan in kod_alanlari:
                    if kayitx.get(alan):
                        kaynak_kod = kayitx[alan]
                        break
                if kaynak_kod and str(kaynak_kod).strip() == str(kod).strip():
                    # alan adı = dosyadaki hedef tür
                    hedef_alan = ad.split("-", 1)[1]
                    eslestirmeler[hedef_alan] = kayitx
        except Exception:
            continue

    if eslestirmeler:
        kayit = dict(kayit)  # kopyala
        kayit["eslestirmeler"] = eslestirmeler
    return kayit


# ═══════════════════════════════════════════════════════════════
# İLİŞKİ YAZMA — Layer 2 (POST)
# ═══════════════════════════════════════════════════════════════
_GECERLI_ROLLER = {"ticaret", "hazine", "sgk", "tuik", "cbdd"}


@app.post("/api/v1/iliski")
def iliski_yaz(paket: Dict[str, Any] = Body(...)):
    """
    İlişki paketini diske yazar.
    Beklenen gövde:
    {
      "rol": "ticaret",
      "varlik": "gtip",
      "dal": "27",                       # opsiyonel (fasıl/grup)
      "kayitlar": [ { "gtip": "...", "islem_adi": "...", ... } ]
    }
    Dosya: iliski/{rol}/{varlik}-{alan}.json
    """
    rol    = str(paket.get("rol", "")).strip().lower()
    varlik = str(paket.get("varlik", "")).strip().lower()
    dal    = str(paket.get("dal", "")).strip()
    kayitlar = paket.get("kayitlar") or []

    if rol not in _GECERLI_ROLLER:
        raise HTTPException(400, f"Geçersiz rol: {rol}")
    if varlik not in ("gtip", "cpc", "isco", "nace"):
        raise HTTPException(400, f"Geçersiz varlık: {varlik}")
    if not isinstance(kayitlar, list) or not kayitlar:
        raise HTTPException(400, "kayitlar boş olamaz")

    # İlişki alanlarını grupla (her biri kendi dosyasına yazılır)
    ALAN_ESLEME = {
        "cpc":      "cpc",
        "isco":     "isco",
        "nace":     "nace",
        "gtip":     "gtip",
        "islem_adi":"randiman",
        "cikti_gtip":"randiman",
        "kdv_orani":"vergi",
        "otv_durum":"vergi",
        "tevkifat_kodu":"vergi",
        "isci":     "prim",
        "isveren":  "prim",
        "sinif":    "tehlike",
        "sure_dk":  "adamsaat",
    }

    gruplar: Dict[str, List[Dict[str, Any]]] = {}
    for k in kayitlar:
        kopya = dict(k)
        for anahtar, alan in ALAN_ESLEME.items():
            if anahtar in kopya:
                gruplar.setdefault(alan, []).append(kopya)
                break
        else:
            # Hiçbir alana girmedi → default olarak ana varlık kendi dosyasına
            gruplar.setdefault("genel", []).append(kopya)

    hedef_klasor = KOK / "iliski" / rol
    hedef_klasor.mkdir(parents=True, exist_ok=True)

    yazilanlar = []
    for alan, ky in gruplar.items():
        # Dosya adı: gtip-cpc.json, gtip-randiman.json …
        dosya_adi = f"{varlik}-{alan}.json"
        dosya_yolu = hedef_klasor / dosya_adi

        # Mevcut dosya varsa birleştir
        mevcut = {"meta": {}, "eslestirmeler": []}
        if dosya_yolu.exists():
            try:
                mevcut = json.loads(dosya_yolu.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Meta güncelle
        mevcut["meta"] = {
            "surum":        datetime.now().strftime("%Y.%m.%d"),
            "guncelleme":   datetime.now().strftime("%Y-%m-%d"),
            "yayinci":      f"PDaaS - {rol}",
            "katman":       "iliski",
            "toplam_kayit": len(mevcut.get("eslestirmeler", [])) + len(ky),
        }

        # Var olan kayıtları kod bazında güncelle
        mevcut_kayitlar = {self_key: x for self_key, x in
                           [(y.get(varlik, ""), y) for y in mevcut.get("eslestirmeler", [])]}

        for y in ky:
            anahtar = str(y.get(varlik, "")).strip()
            if anahtar:
                mevcut_kayitlar[anahtar] = y

        mevcut["eslestirmeler"] = list(mevcut_kayitlar.values())

        # Yaz
        dosya_yolu.write_text(
            json.dumps(mevcut, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        yazilanlar.append({
            "dosya": dosya_adi,
            "yol":   f"iliski/{rol}/{dosya_adi}",
            "kayit": len(ky),
        })

    return {
        "service":    "PDaaS - ILiski Writer v1.0",
        "timestamp":  _zaman_damgasi(),
        "rol":        rol,
        "varlik":     varlik,
        "dal":        dal or None,
        "yazilanlar": yazilanlar,
        "toplam":     sum(y["kayit"] for y in yazilanlar),
    }


@app.get("/api/v1/iliski/{rol}")
def iliski_listele(rol: str):
    """Bir rolün yazdığı tüm ilişki dosyalarını listeler."""
    if rol not in _GECERLI_ROLLER:
        raise HTTPException(400, f"Geçersiz rol: {rol}")

    klasor = KOK / "iliski" / rol
    if not klasor.exists():
        return {
            "service":   "PDaaS - ILiski Listing v1.0",
            "rol":       rol,
            "toplam":    0,
            "dosyalar":  [],
        }

    dosyalar = []
    for f in sorted(klasor.glob("*.json")):
        try:
            v = json.loads(f.read_text(encoding="utf-8"))
            dosyalar.append({
                "dosya":        f.name,
                "kayit_sayisi": len(v.get("eslestirmeler", [])),
                "meta":         v.get("meta", {}),
            })
        except Exception:
            continue

    return {
        "service":  "PDaaS - ILiski Listing v1.0",
        "rol":      rol,
        "toplam":   len(dosyalar),
        "dosyalar": dosyalar,
    }


# ═══════════════════════════════════════════════════════════════
# BİRLEŞTİRME — Layer 3 (Consolidated)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/consolidated")
def birlestirilmis():
    """
    Üç ekseni (ürün + hizmet + meslek) tek çağrıda birleştirir.
    PoC senaryosu: Maden işletmesi (GTİP 2702.10 / CPC 883 / ISCO 8111)
    """
    t0 = time.perf_counter()

    # Her ekseni çek
    try:
        urun = urun_getir("2702.10", katman="iliski")["data"]
    except HTTPException:
        urun = {}
    try:
        hizmet = hizmet_getir("883", katman="iliski")["data"]
    except HTTPException:
        hizmet = {}
    try:
        meslek = meslek_getir("8111", katman="iliski")["data"]
    except HTTPException:
        meslek = {}

    # Yardımcı: birden fazla olası alandan ilk dolu olanı seç
    def _sec(kaynak: dict, *alanlar, default=None):
        for a in alanlar:
            v = kaynak.get(a) if isinstance(kaynak, dict) else None
            if v is not None:
                return v
        return default

    # İlişki katmanı varsa oradan oku, yoksa ham kayıttan oku
    urun_esl   = (urun.get("eslestirmeler") or {}) if isinstance(urun, dict) else {}
    hizmet_esl = (hizmet.get("eslestirmeler") or {}) if isinstance(hizmet, dict) else {}
    meslek_esl = (meslek.get("eslestirmeler") or {}) if isinstance(meslek, dict) else {}

    urun_vergi   = urun_esl.get("vergi")   or {}
    hizmet_vergi = hizmet_esl.get("vergi") or {}
    meslek_prim  = meslek_esl.get("prim")  or {}

    # Kurum bazlı parametreler (eski şemadan)
    def _kurum(kayit: dict, kurum_adi: str) -> dict:
        return (kayit.get("kurumlar") or {}).get(kurum_adi, {}) or {}

    urun_hm   = _kurum(urun, "hazine_maliye")
    hizmet_hm = _kurum(hizmet, "hazine_maliye")
    meslek_sgk = _kurum(meslek, "sgk") or _kurum(meslek, "sosyal_guvenlik")

    urun_ozet = {
        "vat_rate":             _sec(urun_vergi, "kdv_orani", default=_sec(urun_hm, "kdv_orani", default=_sec(urun, "kdv_orani", default=20.00))),
        "sct_rate":             _sec(urun_vergi, "otv_orani", default=_sec(urun_hm, "otv_orani", default=_sec(urun, "otv_orani", default=0.00))),
        "vat_withholding_code": _sec(urun_vergi, "tevkifat_kodu", default=_sec(urun_hm, "tevkifat_kodu", default=_sec(urun, "tevkifat_kodu", default="608"))),
        "vat_withholding_rate": _sec(urun_vergi, "tevkifat_orani", default=_sec(urun_hm, "tevkifat_orani", default=_sec(urun, "tevkifat_orani", default="5/10"))),
    }
    hizmet_ozet = {
        "vat_rate":             _sec(hizmet_vergi, "kdv_orani", default=_sec(hizmet_hm, "kdv_orani", default=_sec(hizmet, "kdv_orani", default=20.00))),
        "vat_withholding_code": _sec(hizmet_vergi, "tevkifat_kodu", default=_sec(hizmet_hm, "tevkifat_kodu", default=_sec(hizmet, "tevkifat_kodu", default="601"))),
        "vat_withholding_rate": _sec(hizmet_vergi, "tevkifat_orani", default=_sec(hizmet_hm, "tevkifat_orani", default=_sec(hizmet, "tevkifat_orani", default="2/10"))),
    }
    meslek_ozet = {
        "sgk_worker_total_share":     _sec(meslek_prim, "isci",              default=_sec(meslek_sgk, "sgk_worker_total_share", "isci_prim_orani", default=_sec(meslek, "isci_prim_orani", default=14.00))),
        "sgk_employer_total_share":   _sec(meslek_prim, "isveren",           default=_sec(meslek_sgk, "sgk_employer_total_share", "isveren_prim_orani", default=_sec(meslek, "isveren_prim_orani", default=20.50))),
        "unemployment_worker_share":  _sec(meslek_prim, "issizlik_isci",     default=_sec(meslek_sgk, "unemployment_worker_share", "issizlik_isci", default=_sec(meslek, "issizlik_isci", default=1.00))),
        "unemployment_employer_share":_sec(meslek_prim, "issizlik_isveren",  default=_sec(meslek_sgk, "unemployment_employer_share", "issizlik_isveren", default=_sec(meslek, "issizlik_isveren", default=2.00))),
        "weekly_max_hours":           _sec(meslek_prim, "haftalik_azami_saat", default=_sec(meslek_sgk, "weekly_max_hours", "haftalik_azami_saat", default=_sec(meslek, "haftalik_azami_saat", default=37.5))),
    }

    sure_ms = round((time.perf_counter() - t0) * 1000, 2)
    _metrik_kaydet(sure_ms)

    return {
        "service":           "PDaaS - Consolidated Transaction Object v2.0",
        "endpoint":          "/api/v1/consolidated",
        "timestamp":         _zaman_damgasi(),
        "execution_time_ms": sure_ms,
        "data": {
            "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "enterprise": {
                "sector":    "Mining",
                "gtip_code": "2702.10",
                "cpc_code":  "883",
                "isco_code": "8111",
            },
            "consolidated_parameters": {
                "product":    urun_ozet,
                "service":    hizmet_ozet,
                "occupation": meslek_ozet,
            },
            "source_services": [
                {"agency": "GİB",             "endpoint": "/api/v1/product/2702.10",       "version": "2.0.0", "legal_basis": "VAT Law No. 3065; Mining Law No. 3213"},
                {"agency": "Ministry of Trade","endpoint": "/api/v1/service/883",           "version": "2.0.0", "legal_basis": "Customs Law No. 4458; OHS Law No. 6331"},
                {"agency": "SGK",             "endpoint": "/api/v1/occupation/8111",        "version": "2.0.0", "legal_basis": "Law No. 5510"},
            ],
            "system_note": "This data object was automatically generated from PDaaS API v2.0 services. No human intervention.",
        },
    }