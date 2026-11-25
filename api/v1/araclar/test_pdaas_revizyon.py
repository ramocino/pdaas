#!/usr/bin/env python3
"""PDaaS revizyon paketinin temel regresyon ve bütünlük testleri."""
from pathlib import Path
import sys, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "araclar"))
from kural_motoru import KuralMotoru, json_checksum

def read(path):
    with (ROOT / path).open(encoding="utf-8") as file:
        return json.load(file)

def test():
    motor = KuralMotoru(ROOT)
    t = motor.konsolide_et("070200910000", akademik=True)
    assert t["vergi"]["kdv"]["yurtici"]["oran"] == 0.01
    assert t["vergi"]["kdv"]["yurtici"]["uygulanabilirlik_durumu"] == "kosul_kontrolu_gerekli"
    for yon in ("yurtici", "ithalat", "ihracat"):
        assert t["vergi"]["otv"][yon]["oran"] is None, yon
        assert t["vergi"]["otv"][yon]["ref"] is None, yon
        assert t["vergi"]["otv"][yon]["uygulanabilirlik_durumu"] == "eslesme_bulunamadi"
    assert t["vergi"]["kdv"]["ihracat"]["oran"] is None
    assert t["vergi"]["kdv"]["ihracat"]["tur"] == "istisna"
    assert t["cpc"][0]["kod"] == "01234"
    assert t["nace"][0]["kod"] == "01.13"
    assert t["isco"] and all(x["iliski_yolu"] == "gtip_nace_isco" for x in t["isco"])
    assert all(b["eslestirme_durumu"] == "kosul_kontrolu_gerekli"
               for b in t["belgeler"]["ithalat"])

    car = motor.konsolide_et("870322101000", akademik=True)
    assert car["vergi"]["kdv"]["yurtici"]["ref"] == "kdv-20"
    assert car["vergi"]["otv"]["yurtici"].get("oran") is None

    for rel in ("ham/kdv.json", "ham/otv.json", "kurallar/vergi-kurallari.json",
                "kurallar/belge-kurallari.json", "kurallar/kod-iliskileri.json",
                "meta/sozluk.json", "meta/katalog.json", "meta/manifest.json",
                "ornek/gtip-070200910000.json", "ornek/gtip-870322101000.json"):
        data=read(rel)
        assert data["meta"]["checksum"] == json_checksum(data), "Checksum: " + rel

    kdv=read("ham/kdv.json")
    assert all(x["oran"] is None for x in kdv["kayitlar"] if x["tur"]=="istisna")
    assert all(x.get("kaynak_ref") and x.get("mevzuat_ref") for x in kdv["kayitlar"])
    otv=read("ham/otv.json")
    notfound=next(x for x in otv["kayitlar"] if x["kod"]=="otv-yok")
    assert notfound["oran"] is None and notfound["teknik_kayit"] is True

    catalog=read("meta/katalog.json")
    assert len(catalog["varliklar"]["konsolide"])==4
    assert len([x for x in catalog["varliklar"]["ornek"]
                if x["dosya"].startswith("ornek/")])==2
    manifest=read("meta/manifest.json")
    sample_paths={x["dosya"] for x in manifest["kaynaklar"]["ornek"]}
    assert "ornek/gtip-070200910000.json" in sample_paths
    view=read("ornek/gtip-070200910000.json")
    assert view["konsolide"]["kod"]=="070200910000"
    assert len(view["kural_ozetleri"])>=2

    expected={"gtip-konsolide.json":15799,"cpc-konsolide.json":2877,
              "nace-konsolide.json":3167,"isco-konsolide.json":436}
    for name,count in expected.items():
        # Toplam büyük dosyayı yeniden yüklemeye gerek kalmadan metadata başlığını
        # küçük bir JSON ayrıştırma yerine katalog + dosya varlığı üzerinden doğruluyoruz.
        path=ROOT/"konsolide"/name
        assert path.is_file() and path.stat().st_size>10000, name
        entry=next(x for x in catalog["varliklar"]["konsolide"] if x["dosya"].endswith(name))
        assert entry["kayit_sayisi"]==count,(name,entry["kayit_sayisi"])
    print("PASS: 2 ürün; 4 konsolide set; KDV/ÖTV/istisna; kaynak-kural-iz; belge; sınıflama; SHA-256")
if __name__=="__main__":
    test()
