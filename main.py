"""
PDaaS API — Parametric Data as a Service
Otomatik servis keşfi: ham/ altındaki her JSON kendi meta bloğuyla
hangi bakanlığa ait olduğunu ve servis kodunu bildirir.

Performance v14:
- GZip sıkıştırma (JSON %85-90 küçülür)
- Bellek içi JSON cache (lru_cache) — disk I/O yok
- HTTP Cache-Control başlıkları (tarayıcı önbelleği)
- Çift dilli meta alanları (bakanlik_adi_en, servis_adi_en, kaynak_en)
"""
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict
from functools import lru_cache
import json, time
from datetime import datetime, timezone

BUILD_VERSION = "v14_i18n_meta_2026_10_14"
BUILD_TIMESTAMP = "2026-10-14T12:00:00Z"

app = FastAPI(
    title="PDaaS API",
    version="3.4.0",
    description="Parametric Data as a Service — Turkish public parameters (recursive auto-discovery)",
)

# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
# GZip en dış katman → tüm yanıtları sıkıştırır
app.add_middleware(GZipMiddleware, minimum_size=500)

KOK = Path(__file__).parent
HAM_KOK = KOK / "ham"
_METRICS = {"requests": 0, "total_ms": 0.0, "max_ms": 0.0}
_SERVIS_KATALOGU: Dict[tuple, dict] = {}

# ═══════════════════════════════════════════════════════════════
# STATİK DOSYA
# ═══════════════════════════════════════════════════════════════
if HAM_KOK.exists():
    app.mount("/ham", StaticFiles(directory=str(HAM_KOK)), name="ham")

# ═══════════════════════════════════════════════════════════════
# YARDIMCILAR + BELLEK CACHE
# ═══════════════════════════════════════════════════════════════
def _zaman_damgasi() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _metrik_kaydet(sure_ms: float):
    _METRICS["requests"] += 1
    _METRICS["total_ms"] += sure_ms
    if sure_ms > _METRICS["max_ms"]:
        _METRICS["max_ms"] = sure_ms


@lru_cache(maxsize=None)
def _json_oku_cache(yol_str: str):
    """
    JSON dosyasını belleğe alır. Process ömrü boyunca cache'lenir.
    Not: Dosya diskte değişirse yeniden başlatılana kadar eski hâli döner.
    """
    try:
        return json.loads(Path(yol_str).read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _json_oku(yol: Path):
    """Path sarmalayıcı → cache'lenmiş versiyona yönlendirir."""
    return _json_oku_cache(str(yol))


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
# BAKANLIK ADI HARİTASI (TR + EN)
# ═══════════════════════════════════════════════════════════════
_BAKANLIK_ADLARI = {
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

_BAKANLIK_ADLARI_EN = {
    "tb":       "Republic of Türkiye Ministry of Trade",
    "hvmb":     "Republic of Türkiye Ministry of Treasury and Finance",
    "hazine":   "Republic of Türkiye Ministry of Treasury and Finance",
    "csgb":     "Republic of Türkiye Ministry of Labour and Social Security",
    "sgk":      "Social Security Institution",
    "tuik":     "Turkish Statistical Institute",
    "csidb":    "Republic of Türkiye Ministry of Environment, Urbanisation and Climate Change",
    "etkb":     "Republic of Türkiye Ministry of Energy and Natural Resources",
    "genel":    "General Reference Data",
}


# ═══════════════════════════════════════════════════════════════
# OTOMATİK KATALOG TARAMASI
# ═══════════════════════════════════════════════════════════════
def _katalog_tara() -> dict:
    _SERVIS_KATALOGU.clear()
    if not HAM_KOK.exists():
        return _SERVIS_KATALOGU

    for f in sorted(HAM_KOK.rglob("*.json")):
        veri = _json_oku(f)  # cache'den
        if not isinstance(veri, dict):
            continue

        meta = veri.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}

        dosya_stem = f.stem.lower()
        rel = f.relative_to(HAM_KOK)
        parts = rel.parts

        bak = (meta.get("bakanlik") or "").strip().lower()
        if not bak:
            bak = parts[0].strip().lower() if len(parts) > 1 else "genel"

        # TR / EN bakanlık adı — meta'dan gel, yoksa sözlükten, yoksa koddan
        bakanlik_adi = (
            meta.get("bakanlik_adi")
            or _BAKANLIK_ADLARI.get(bak)
            or bak.upper()
        )
        bakanlik_adi_en = (
            meta.get("bakanlik_adi_en")
            or _BAKANLIK_ADLARI_EN.get(bak)
            or bakanlik_adi
        )

        svc = (meta.get("servis_kodu") or "").strip().lower()
        if not svc:
            svc = f"{parts[0]}-{dosya_stem}".lower() if len(parts) > 1 else dosya_stem.lower()

        servis_adi = meta.get("servis_adi") or dosya_stem.replace("-", " ").title()
        servis_adi_en = meta.get("servis_adi_en") or servis_adi

        anahtar = (bak, svc)
        k = _SERVIS_KATALOGU.get(anahtar)
        if not k:
            k = {
                "bakanlik":              bak,
                "bakanlik_adi":          bakanlik_adi,
                "bakanlik_adi_en":       bakanlik_adi_en,
                "servis_kodu":           svc,
                "servis_adi":            servis_adi,
                "servis_adi_en":         servis_adi_en,
                "tip":                   (meta.get("tip") or "agac").lower(),
                "join":                  meta.get("join") or "kod",
                "surum":                 meta.get("surum") or meta.get("dosya_surumu") or "2026.01.01",
                "yayinci":               meta.get("yayinci"),
                "yayinci_en":            meta.get("yayinci_en"),
                "kaynak":                meta.get("kaynak"),
                "kaynak_en":             meta.get("kaynak_en"),
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
    """Hem TR hem EN meta alanlarını dışa verir."""
    return {
        "bakanlik":             k["bakanlik"],
        "bakanlik_adi":         k["bakanlik_adi"],
        "bakanlik_adi_en":      k.get("bakanlik_adi_en"),
        "servis_kodu":          k["servis_kodu"],
        "servis_adi":           k["servis_adi"],
        "servis_adi_en":        k.get("servis_adi_en"),
        "surum":                k["surum"],
        "yayinci":              k.get("yayinci"),
        "yayinci_en":           k.get("yayinci_en"),
        "kaynak":               k.get("kaynak"),
        "kaynak_en":            k.get("kaynak_en"),
        "gecerlilik_baslangic": k.get("gecerlilik_baslangic"),
        "gecerlilik_bitis":     k.get("gecerlilik_bitis"),
    }


def _servis_bul(bakanlik: str, servis_kodu: str) -> dict:
    bak_aranan = bakanlik.lower()
    svc_aranan = servis_kodu.lower()

    k = _SERVIS_KATALOGU.get((bak_aranan, svc_aranan))
    if k:
        return k

    for (b, s), kayit in _SERVIS_KATALOGU.items():
        if s == svc_aranan or s.replace("-", "") == svc_aranan.replace("-", ""):
            return kayit

    _katalog_tara()
    for (b, s), kayit in _SERVIS_KATALOGU.items():
        if s == svc_aranan or s.replace("-", "") == svc_aranan.replace("-", ""):
            return kayit

    raise HTTPException(404, f"Servis bulunamadı: {bakanlik}/{servis_kodu}")


# ═══════════════════════════════════════════════════════════════
# HTML SAYFALARI
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# HTML SAYFALARI — uzantısız + uzantılı alias
# ═══════════════════════════════════════════════════════════════
def _html_serve(dosya_adi: str, response: Response = None):
    """HTML sayfasını güvenli şekilde döner; 404'te bilgi verir."""
    yol = KOK / dosya_adi
    if not yol.exists():
        raise HTTPException(404, f"{dosya_adi} bulunamadı")
    # HTML sayfalarını 5 dk tarayıcı cache'ine al (hızlı gezinme)
    if response is not None:
        response.headers["Cache-Control"] = "public, max-age=300"
    return FileResponse(yol, media_type="text/html; charset=utf-8")


# ─── Ana sayfa (Portal) ───
@app.get("/", include_in_schema=False)
def ana_sayfa(response: Response):
    return _html_serve("index.html", response)

@app.get("/index", include_in_schema=False)
def ana_sayfa_kisa(response: Response):
    return _html_serve("index.html", response)

@app.get("/index.html", include_in_schema=False)
def ana_sayfa_html(response: Response):
    return _html_serve("index.html", response)


# ─── Ürün Arama ───
@app.get("/urunler", include_in_schema=False)
def urunler_sayfasi(response: Response):
    return _html_serve("urunler.html", response)

@app.get("/urunler.html", include_in_schema=False)
def urunler_sayfasi_html(response: Response):
    return _html_serve("urunler.html", response)


# ─── Küratör ───
@app.get("/kurator", include_in_schema=False)
def kurator_sayfasi(response: Response):
    return _html_serve("kurator.html", response)

@app.get("/kurator.html", include_in_schema=False)
def kurator_sayfasi_html(response: Response):
    return _html_serve("kurator.html", response)

# ═══════════════════════════════════════════════════════════════
# API ENDPOINT'LERİ
# ═══════════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "healthy", "build": BUILD_VERSION}


@app.get("/api/v1/katalog")
def katalog_listesi(response: Response):
    _katalog_tara()

    servisler = []
    for (bak, svc), k in sorted(_SERVIS_KATALOGU.items()):
        toplam = sum(d["kayit_sayisi"] for d in k["dosyalar"])
        servisler.append({
            "bakanlik":             bak,
            "bakanlik_adi":         k["bakanlik_adi"],
            "bakanlik_adi_en":      k.get("bakanlik_adi_en"),
            "servis_kodu":          svc,
            "servis_adi":           k["servis_adi"],
            "servis_adi_en":        k.get("servis_adi_en"),
            "tip":                  k["tip"],
            "join":                 k["join"],
            "surum":                k["surum"],
            "yayinci":              k.get("yayinci"),
            "yayinci_en":           k.get("yayinci_en"),
            "kaynak":               k.get("kaynak"),
            "kaynak_en":            k.get("kaynak_en"),
            "gecerlilik_baslangic": k.get("gecerlilik_baslangic"),
            "dosya_sayisi":         len(k["dosyalar"]),
            "kayit_sayisi":         toplam,
            "endpoint":             f"/api/v1/{bak}/{svc}",
        })

    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=3600"
    response.headers["Vary"] = "Accept-Encoding"

    return {
        "service":   "PDaaS - Auto Catalog",
        "timestamp": _zaman_damgasi(),
        "toplam":    len(servisler),
        "servisler": servisler,
    }


@app.get("/api/v1/{bakanlik}/{servis_kodu}")
def servis_ozet(bakanlik: str, servis_kodu: str, response: Response):
    t0 = time.perf_counter()
    try:
        k = _servis_bul(bakanlik, servis_kodu)

        response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
        response.headers["Vary"] = "Accept-Encoding"

        tip = k.get("tip", "").lower()

        # ═══════════════════════════════════════════════════════
        # HARİTA TİPİ: {gruplar, kurallar} tam yapısını koru
        # (gtip-ozel-izin-belge, gtip-randiman, cpc-ozel-izin-belge, vb.)
        # ═══════════════════════════════════════════════════════
        if tip == "harita":
            tum_gruplar = {}
            tum_kurallar = []
            for d in k["dosyalar"]:
                v = _json_oku(d["yol"])
                if not v:
                    continue
                if isinstance(v.get("gruplar"), dict):
                    tum_gruplar.update(v["gruplar"])
                if isinstance(v.get("kurallar"), list):
                    tum_kurallar.extend(v["kurallar"])

            _metrik_kaydet((time.perf_counter() - t0) * 1000)

            return {
                **_ortak_meta(k),
                "tip": "harita",
                "join": k["join"],
                "toplam": len(tum_kurallar),
                "gruplar": tum_gruplar,
                "kurallar": tum_kurallar,
            }

        # ═══════════════════════════════════════════════════════
        # SÖZLÜK TİPİ: {kurumlar: {...}, tipler: {...}} yapısını koru
        # (kurumlar.json, ileride eklenecek diğer sözlükler)
        # ═══════════════════════════════════════════════════════
        if tip == "sozluk":
            birlestirilmis = {}
            for d in k["dosyalar"]:
                v = _json_oku(d["yol"])
                if not v or not isinstance(v, dict):
                    continue
                for anahtar, deger in v.items():
                    if anahtar == "meta":
                        continue
                    if isinstance(deger, dict) and anahtar in birlestirilmis:
                        birlestirilmis[anahtar].update(deger)
                    else:
                        birlestirilmis[anahtar] = deger

            _metrik_kaydet((time.perf_counter() - t0) * 1000)

            return {
                **_ortak_meta(k),
                "tip": "sozluk",
                "join": k["join"],
                **birlestirilmis,
            }

        # ═══════════════════════════════════════════════════════
        # LİSTE / AĞAÇ TİPİ: mevcut davranış (kayitlar array'i)
        # (gtip-kodlari, kdv-oranlari, nace-kodlari, vb.)
        # ═══════════════════════════════════════════════════════
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
            "kayitlar": tum,
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f"Sunucu hatası: {str(e)}")


@app.get("/api/v1/metrics", include_in_schema=False)
def metrics():
    """Basit performans metrikleri (opsiyonel)."""
    ort = (_METRICS["total_ms"] / _METRICS["requests"]) if _METRICS["requests"] else 0
    return {
        "requests":    _METRICS["requests"],
        "ortalama_ms": round(ort, 2),
        "max_ms":      round(_METRICS["max_ms"], 2),
        "cache_info":  str(_json_oku_cache.cache_info()),
    }