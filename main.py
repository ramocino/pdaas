from fastapi import FastAPI, HTTPException
from pathlib import Path
import json
from datetime import datetime, timezone

app = FastAPI(
    title="PDaaS API",
    version="1.0.0",
    description="Parametric Data as a Service - Turkish public parameters",
)

# Proje kök dizini (main.py'nin bulunduğu yer)
KOK = Path(__file__).parent

def dosya_oku(rel_yol: str) -> dict:
    """JSON dosyasını okur ve hata durumunda 404 döndürür."""
    yol = KOK / rel_yol
    if not yol.exists():
        raise HTTPException(404, f"Veri dosyası bulunamadı: {rel_yol}")
    return json.loads(yol.read_text(encoding="utf-8"))

@app.get("/")
def kok():
    return {
        "service": "PDaaS API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": ["/health", "/stats", "/api/v1/product/{gtip_code}"],
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

@app.get("/stats")
def stats():
    """manifest.json'dan istatistikleri döndürür."""
    manifest = dosya_oku("manifest.json")
    return manifest.get("istatistik", {})

@app.get("/api/v1/product/{gtip_code}")
def urun_getir(gtip_code: str):
    """
    GTİP koduna göre ürün parametrelerini döndürür.
    Örnek: /api/v1/product/2702.10
    """
    # GTİP kodundan fasıl numarasını çıkar (ilk 2 hane, sıfırla doldur)
    temiz = gtip_code.replace(".", "")
    if len(temiz) < 2:
        raise HTTPException(400, "Geçersiz GTİP kodu")
    fasil = temiz[:2].zfill(2)

    # İlgili fasıl dosyasını oku
    veri = dosya_oku(f"ticaret/gtip/{fasil}.json")

    # Kayıtlar içinde kodu ara
    kayit = next((k for k in veri.get("kayitlar", []) if k.get("kod") == gtip_code), None)
    if not kayit:
        raise HTTPException(404, f"GTİP kodu bulunamadı: {gtip_code}")

    return {
        "service": "PDaaS - Product Service v1.0",
        "endpoint": f"/api/v1/product/{gtip_code}",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "version_id": veri.get("surum", "1.0.0"),
        "valid_from": veri.get("yururluk_baslangic"),
        "valid_to": veri.get("yururluk_bitis"),
        "legal_basis_doc": veri.get("kaynak"),
        "data": kayit,  # Ham kayıt (27.json'daki tüm alanlar)
    }
