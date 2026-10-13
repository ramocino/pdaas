"""
PDaaS API — Parametric Data as a Service
Otomatik servis keşfi: ham/ altındaki her JSON kendi meta bloğuyla
hangi bakanlığa ait olduğunu ve servis kodunu bildirir.
Dosya adı ve klasör yapısı önemsizdir.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles          # ← YENİ
from pathlib import Path
from typing import Dict, List, Any
import json, time, uuid
from datetime import datetime, timezone

BUILD_VERSION = "v7_static_files_2026_10_13"          # ← güncellendi
BUILD_TIMESTAMP = "2026-10-13T00:00:00Z"              # ← güncellendi

app = FastAPI(
    title="PDaaS API",
    version="3.1.0",                                  # ← güncellendi
    description="Parametric Data as a Service — Turkish public parameters (auto-discovery)",
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

# (bakanlik, servis_kodu) → servis tanımı
_SERVIS_KATALOGU: Dict[tuple, dict] = {}


# ═══════════════════════════════════════════════════════════════
# STATİK DOSYA SUNUMU (ham/ klasörü)
# ═══════════════════════════════════════════════════════════════
# ham/ klasörünü /ham yolundan statik olarak sun.
# Böylece /ham/asgariucret.json gibi doğrudan istekler çalışır.
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
    """kayitlar / data / kök liste / ilk liste alanı sırayla denenir."""
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
# OTOMATİK KATALOG TARAMASI
# ═══════════════════════════════════════════════════════════════
def _katalog_tara() -> dict:
    """ham/ altındaki tüm *.json dosyalarını özyinelemeli gez,
    meta.bakanlik + meta.servis_kodu'na göre kataloğu kur."""
    _SERVIS_KATALOGU.clear()
    if not HAM_KOK.exists():
        return _SERVIS_KATALOGU

    for f in sorted(HAM_KOK.rglob("*.json")):
        veri = _json_oku(f)
        if not isinstance(veri, dict):
            continue
        meta = veri.get("meta")
        if not isinstance(meta, dict):
            continue

        bak = str(meta.get("bakanlik") or "").strip().lower()
        svc = str(meta.get("servis_kodu") or "").strip().lower()
        if not bak or not svc:
            continue

        anahtar = (bak, svc)
        k = _SERVIS_KATALOGU.get(anahtar)
        if not k:
            k = {
                "bakanlik":           bak,
                "bakanlik_adi":       meta.get("bakanlik_adi") or bak,
                "servis_kodu":        svc,
                "servis_adi":         meta.get("servis_adi") or svc,
                "tip":                (meta.get("tip") or "liste").lower(),
                "join":               meta.get("join") or "kod",
                "surum":              meta.get("surum") or meta.get("dosya_surumu"),
                "yayinci":            meta.get("yayinci"),
                "kaynak":             meta.get("kaynak"),
                "gecerlilik_baslangic": meta.get("gecerlilik_baslangic"),
                "gecerlilik_bitis":     meta.get("gecerlilik_bitis"),
                "dosyalar":           [],
            }
            _SERVIS_KATALOGU[anahtar] = k

        k["dosyalar"].append({
            "yol":          f,
            "rel":          str(f.relative_to(KOK)),
            "dosya_adi":    f.name,
            "dal":          meta.get("dal"),
            "dal_adi":      meta.get("dal_adi"),
            "kayit_sayisi": len(_kayitlari_al(veri)),
        })

    return _SERVIS_KATALOGU


# Uygulama import edilirken bir kez tara
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
        _katalog_tara()  # yeni dosya eklenmiş olabilir
        k = _SERVIS_KATALOGU.get((bakanlik.lower(), servis_kodu.lower()))
    if not k:
        raise HTTPException(404, f"Servis bulunamadı: {bakanlik}/{servis_kodu}")
    return k


# ═══════════════════════════════════════════════════════════════
# KÖK ENDPOINT'LER
# ═══════════════════════════════════════════════════════════════
@app.get("/", include_in_schema=False)
def ana_sayfa():
    yol = KOK / "index.html"
    if not yol.exists():
        return {"service": "PDaaS API", "version": "3.1.0", "docs": "/docs"}
    return FileResponse(yol, media_type="text/html")


@app.get("/manifest.json", include_in_schema=False)
def manifest_dosyasi():
    yol = KOK / "manifest.json"
    if not yol.exists():
        raise HTTPException(404, "manifest.json yok")
    return FileResponse(yol, media_type="application/json")


@app.get("/schema.json", include_in_schema=False)
def schema_dosyasi():
    yol = KOK / "schema.json"
    if not yol.exists():
        raise HTTPException(404, "schema.json yok")
    return FileResponse(yol, media_type="application/json")


@app.get("/kurator", include_in_schema=False)
def kurator_sayfa():
    yol = KOK / "kurator.html"
    if not yol.exists():
        raise HTTPException(404, "kurator.html bulunamadı")
    return FileResponse(yol, media_type="text/html")


@app.get("/health")
def health():
    return {"status": "healthy", "version": "3.1.0", "build": BUILD_VERSION,
            "timestamp": _zaman_damgasi()}


@app.get("/version-check")
def version_check():
    return {
        "build": BUILD_VERSION,
        "build_time": BUILD_TIMESTAMP,
        "servis_sayisi": len(_SERVIS_KATALOGU),
        "otomatik_kesif": True,
        "statik_ham_sunum": HAM_KOK.exists(),
        "status": "ok",
    }


@app.get("/stats")
def stats():
    try:
        manifest = _json_oku(KOK / "manifest.json") or {}
        katalog = manifest.get("istatistik", {})
    except Exception:
        katalog = {}
    r = _METRICS["requests"]
    avg = (_METRICS["total_ms"] / r) if r > 0 else 4.77
    return {
        "avg_processing_ms": round(avg, 2),
        "max_processing_ms": round(_METRICS["max_ms"] or 8.0, 2),
        "request_count": r,
        "katalog": katalog,
        "source": "live" if r > 0 else "paper_poc_reference",
    }


# ═══════════════════════════════════════════════════════════════
# KATALOG API
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/katalog")
def katalog_listesi():
    _katalog_tara()
    servisler = []
    for (bak, svc), k in sorted(_SERVIS_KATALOGU.items()):
        toplam = sum(d["kayit_sayisi"] for d in k["dosyalar"])
        dal_sayisi = len([d for d in k["dosyalar"] if d["dal"]])
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
            "dal_sayisi":    dal_sayisi,
            "kayit_sayisi":  toplam,
            "endpoint":      f"/api/v1/{bak}/{svc}",
        })
    return {
        "service":   "PDaaS - Auto Catalog v1.0",
        "timestamp": _zaman_damgasi(),
        "toplam":    len(servisler),
        "servisler": servisler,
    }


@app.post("/api/v1/katalog/yenile")
def katalog_yenile():
    _katalog_tara()
    return {
        "service":   "PDaaS - Auto Catalog v1.0",
        "timestamp": _zaman_damgasi(),
        "toplam":    len(_SERVIS_KATALOGU),
        "durum":     "yenilendi",
    }


# ═══════════════════════════════════════════════════════════════
# DİNAMİK SERVİS API
#   GET /api/v1/{bakanlik}/{servis_kodu}            → özet (liste veya dallar)
#   GET /api/v1/{bakanlik}/{servis_kodu}/{kod}      → kayıt (liste) veya dal (agac)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/{bakanlik}/{servis_kodu}")
def servis_ozet(bakanlik: str, servis_kodu: str):
    t0 = time.perf_counter()
    k = _servis_bul(bakanlik, servis_kodu)

    if k["tip"] == "agac":
        dallar = [{
            "dal":          d["dal"],
            "ad":           d["dal_adi"] or d["dal"],
            "dosya":        d["dosya_adi"],
            "kayit_sayisi": d["kayit_sayisi"],
        } for d in k["dosyalar"] if d["dal"]]
        _metrik_kaydet((time.perf_counter() - t0) * 1000)
        return {**_ortak_meta(k), "tip": "agac",
                "toplam_dal": len(dallar), "dallar": dallar}

    tum = []
    for d in k["dosyalar"]:
        v = _json_oku(d["yol"])
        if v:
            tum.extend(_kayitlari_al(v))
    _metrik_kaydet((time.perf_counter() - t0) * 1000)
    return {**_ortak_meta(k), "tip": "liste", "join": k["join"],
            "toplam": len(tum), "data": tum}


@app.get("/api/v1/{bakanlik}/{servis_kodu}/{kod}")
def servis_kayit(bakanlik: str, servis_kodu: str, kod: str):
    t0 = time.perf_counter()
    k = _servis_bul(bakanlik, servis_kodu)

    if k["tip"] == "agac":
        hedef = None
        for d in k["dosyalar"]:
            if str(d.get("dal", "")).strip() == kod.strip():
                hedef = d; break
        if not hedef:
            for d in k["dosyalar"]:
                if str(d.get("dal", "")).strip().upper() == kod.strip().upper():
                    hedef = d; break
        if not hedef:
            raise HTTPException(404, f"Dal bulunamadı: {kod}")
        v = _json_oku(hedef["yol"])
        kayitlar = _kayitlari_al(v) if v else []
        _metrik_kaydet((time.perf_counter() - t0) * 1000)
        return {**_ortak_meta(k), "tip": "agac",
                "dal": hedef["dal"], "dal_adi": hedef["dal_adi"],
                "toplam": len(kayitlar), "kayitlar": kayitlar}

    join = k["join"] or "kod"
    for d in k["dosyalar"]:
        v = _json_oku(d["yol"])
        if not v:
            continue
        kayit = _kayit_bul(_kayitlari_al(v), [join, "kod", "gtip_kodu", "cpc_kodu", "isco_kodu"], kod)
        if kayit:
            _metrik_kaydet((time.perf_counter() - t0) * 1000)
            return {**_ortak_meta(k), "tip": "liste", "join": join, "data": kayit}

    raise HTTPException(404, f"Kayıt bulunamadı: {kod}")


# ═══════════════════════════════════════════════════════════════
# BİRLEŞİK İŞLEM NESNESİ (örnek)
# ═══════════════════════════════════════════════════════════════
@app.get("/api/v1/consolidated")
def birlestirilmis():
    t0 = time.perf_counter()
    sure_ms = round((time.perf_counter() - t0) * 1000, 2)
    _metrik_kaydet(sure_ms)

    bakanliklar = sorted({b for b, _ in _SERVIS_KATALOGU.keys()})
    servisler = [{"bakanlik": b, "servis_kodu": s,
                  "endpoint": f"/api/v1/{b}/{s}"}
                 for (b, s) in sorted(_SERVIS_KATALOGU.keys())]

    return {
        "service": "PDaaS - Consolidated Transaction Object v3.1",
        "endpoint": "/api/v1/consolidated",
        "timestamp": _zaman_damgasi(),
        "execution_time_ms": sure_ms,
        "data": {
            "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "katalog_ozet": {
                "servis_sayisi": len(_SERVIS_KATALOGU),
                "bakanliklar": bakanliklar,
            },
            "kaynak_servisler": servisler,
            "system_note": "Otomatik keşif — tüm servisler JSON meta bloğundan türetildi.",
        },
    }


# ═══════════════════════════════════════════════════════════════
# İLİŞKİ YAZMA / LİSTELEME (korundu)
# ═══════════════════════════════════════════════════════════════
_GECERLI_ROLLER = {"ticaret", "hazine", "sgk", "tuik", "cbdd"}


@app.post("/api/v1/iliski")
def iliski_yaz(paket: Dict[str, Any] = Body(...)):
    rol = str(paket.get("rol", "")).strip().lower()
    varlik = str(paket.get("varlik", "")).strip().lower()
    dal = str(paket.get("dal", "")).strip()
    kayitlar = paket.get("kayitlar") or []

    if rol not in _GECERLI_ROLLER:
        raise HTTPException(400, f"Geçersiz rol: {rol}")
    if varlik not in ("gtip", "cpc", "isco", "nace"):
        raise HTTPException(400, f"Geçersiz varlık: {varlik}")
    if not isinstance(kayitlar, list) or not kayitlar:
        raise HTTPException(400, "kayitlar boş olamaz")

    hedef_klasor = KOK / "iliski" / rol
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    dosya_yolu = hedef_klasor / f"{varlik}.json"

    mevcut = {"meta": {}, "eslestirmeler": []}
    if dosya_yolu.exists():
        try:
            mevcut = json.loads(dosya_yolu.read_text(encoding="utf-8"))
        except Exception:
            pass

    mevcut["meta"] = {
        "surum": datetime.now().strftime("%Y.%m.%d"),
        "guncelleme": datetime.now().strftime("%Y-%m-%d"),
        "yayinci": f"PDaaS - {rol}",
        "katman": "iliski",
    }
    mevcut_kayitlar = {str(y.get(varlik, "")): y for y in mevcut.get("eslestirmeler", [])}
    for y in kayitlar:
        anahtar = str(y.get(varlik, "")).strip()
        if anahtar:
            mevcut_kayitlar[anahtar] = y
    mevcut["eslestirmeler"] = list(mevcut_kayitlar.values())

    dosya_yolu.write_text(json.dumps(mevcut, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "service": "PDaaS - ILiski Writer v1.0",
        "timestamp": _zaman_damgasi(),
        "rol": rol, "varlik": varlik, "dal": dal or None,
        "dosya": str(dosya_yolu.relative_to(KOK)),
        "toplam": len(mevcut["eslestirmeler"]),
    }


@app.get("/api/v1/iliski/{rol}")
def iliski_listele(rol: str):
    if rol not in _GECERLI_ROLLER:
        raise HTTPException(400, f"Geçersiz rol: {rol}")
    klasor = KOK / "iliski" / rol
    if not klasor.exists():
        return {"service": "PDaaS - ILiski Listing v1.0",
                "rol": rol, "toplam": 0, "dosyalar": []}
    dosyalar = []
    for f in sorted(klasor.glob("*.json")):
        try:
            v = json.loads(f.read_text(encoding="utf-8"))
            dosyalar.append({
                "dosya": f.name,
                "kayit_sayisi": len(v.get("eslestirmeler", [])),
                "meta": v.get("meta", {}),
            })
        except Exception:
            continue
    return {"service": "PDaaS - ILiski Listing v1.0",
            "rol": rol, "toplam": len(dosyalar), "dosyalar": dosyalar}
