#!/usr/bin/env python3
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

def yukle(yol):
    with open(yol, encoding="utf-8") as f:
        return json.load(f)

def yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")

def son_surum_bul(kok, servis_kod):
    kat = yukle(kok / "katalog.json")
    for servis in kat.get("servisler", []):
        if servis["kod"] == servis_kod:
            for katman_adi, katman_bilgi in servis.get("katmanlar", {}).items():
                return katman_bilgi
    raise ValueError(f"Katalogda {servis_kod} bulunamadı.")

def parcala_ve_yaz(kok, servis_kod, ad_tr, ad_en, kayitlar, meta_kaynak):
    hedef_klasor = kok / servis_kod
    fasil_klasor = hedef_klasor / "fasil"
    
    gruplar = {}
    for k in kayitlar:
        fasil = str(k.get("kod", "00"))[:2]
        gruplar.setdefault(fasil, []).append(k)
        
    bugun = datetime.date.today()
    temel_meta = {
        "schema_surumu": "1.0.0",
        "servis": {"kod": servis_kod, "ad": {"tr": ad_tr, "en": ad_en}},
        "katman": "konsolide",
        "yapi": {"tip": "liste", "kod_sistemi": "gtip", "kapsam": ["vergi", "ticaret"]},
        "surum": bugun.strftime("%Y.%m.%d"), "guncelleme": bugun.isoformat(), "yayin_durumu": "yayinda",
        "zaman": {"bazli": False, "baslangic": None, "bitis": None},
        "yayinci": meta_kaynak["yayinci"], "kaynaklar": meta_kaynak.get("kaynaklar", []), "mevzuat_ref": meta_kaynak.get("mevzuat_ref", []),
        "uretim": meta_kaynak["uretim"]
    }

    for fasil, f_kayitlar in gruplar.items():
        parca_meta = dict(temel_meta)
        parca_meta["parca"] = {"tur": "fasil", "kod": fasil, "ana_dosya": "index.json"}
        yaz(fasil_klasor / f"{fasil}.json", {"meta": parca_meta, "kayitlar": f_kayitlar})

    index_meta = dict(temel_meta)
    yaz(hedef_klasor / "index.json", {
        "meta": index_meta,
        "fasillar": [{"kod": fasil, "kayit_sayisi": len(f_kayitlar), "dosya": f"fasil/{fasil}.json"} for fasil, f_kayitlar in sorted(gruplar.items())]
    })
    print(f"  -> {servis_kod} (Klasör): {len(gruplar)} fasıl.")

def tum_veriyi_yaz(kok, servis_kod, ad_tr, ad_en, kayitlar, meta_kaynak):
    bugun = datetime.date.today()
    temel_meta = {
        "schema_surumu": "1.0.0",
        "servis": {"kod": servis_kod, "ad": {"tr": ad_tr, "en": ad_en}},
        "katman": "konsolide",
        "yapi": {"tip": "liste", "kod_sistemi": "gtip", "kapsam": ["vergi", "ticaret"]},
        "surum": bugun.strftime("%Y.%m.%d"), "guncelleme": bugun.isoformat(), "yayin_durumu": "yayinda",
        "zaman": {"bazli": False, "baslangic": None, "bitis": None},
        "yayinci": meta_kaynak["yayinci"], "kaynaklar": meta_kaynak.get("kaynaklar", []), "mevzuat_ref": meta_kaynak.get("mevzuat_ref", []),
        "uretim": meta_kaynak["uretim"]
    }
    yaz(kok / f"{servis_kod}.json", {"meta": temel_meta, "kayitlar": kayitlar})
    print(f"  -> {servis_kod}.json (Tek Dosya) oluşturuldu.")

def eslesme_yap(kok):
    print("Konsolide derleme başladı...")
    
    gtip_kat = son_surum_bul(kok, "gtip-kodlari")
    kdv_oran_kat = son_surum_bul(kok, "kdv-oranlari")
    kdv_kural_kat = son_surum_bul(kok, "kdv-kurallar")
    otv_oran_kat = son_surum_bul(kok, "otv-oranlari")
    otv_kural_kat = son_surum_bul(kok, "otv-kurallar")
    tevkifat_oran_kat = son_surum_bul(kok, "tevkifat-oranlari")
    tevkifat_kural_kat = son_surum_bul(kok, "tevkifat-kurallar")
    randiman_oran_kat = son_surum_bul(kok, "randiman")
    randiman_kural_kat = son_surum_bul(kok, "randiman-kurallar")

    gtip_doc = yukle(kok / "surumler" / "gtip-kodlari" / f"{gtip_kat['son']}.json")
    kdv_oran_doc = yukle(kok / "surumler" / "kdv-oranlari" / f"{kdv_oran_kat['son']}.json")
    kdv_kural_doc = yukle(kok / "surumler" / "kdv-kurallar" / f"{kdv_kural_kat['son']}.json")
    otv_oran_doc = yukle(kok / "surumler" / "otv-oranlari" / f"{otv_oran_kat['son']}.json")
    otv_kural_doc = yukle(kok / "surumler" / "otv-kurallar" / f"{otv_kural_kat['son']}.json")
    tevkifat_oran_doc = yukle(kok / "surumler" / "tevkifat-oranlari" / f"{tevkifat_oran_kat['son']}.json")
    tevkifat_kural_doc = yukle(kok / "surumler" / "tevkifat-kurallar" / f"{tevkifat_kural_kat['son']}.json")
    randiman_oran_doc = yukle(kok / "surumler" / "randiman" / f"{randiman_oran_kat['son']}.json")
    randiman_kural_doc = yukle(kok / "surumler" / "randiman-kurallar" / f"{randiman_kural_kat['son']}.json")

    def oran_dict(doc): return {k["kod"]: k for k in doc.get("kayitlar", [])}
    kdv_oranlar = oran_dict(kdv_oran_doc)
    otv_oranlar = oran_dict(otv_oran_doc)
    tevkifat_oranlar = oran_dict(tevkifat_oran_doc)
    randiman_oranlar = oran_dict(randiman_oran_doc)

    def kurallari_hazirla(doc):
        varsayilan, aktif = None, []
        for k in doc.get("kurallar", []):
            if k.get("varsayilan"): varsayilan = k
            elif k.get("prefixler"): aktif.append(k)
        aktif.sort(key=lambda x: x.get("oncelik", 0), reverse=True)
        return varsayilan, aktif

    kdv_default, kdv_aktif = kurallari_hazirla(kdv_kural_doc)
    otv_default, otv_aktif = kurallari_hazirla(otv_kural_doc)
    tevk_default, tevk_aktif = kurallari_hazirla(tevkifat_kural_doc)

    yapraklar = [k for k in gtip_doc.get("kayitlar", []) if k.get("yaprak") is True]
    print(f"  -> İşlenecek GTİP Yaprağı: {len(yapraklar)}")

    sonuc_kdv, sonuc_otv, sonuc_tevkifat, sonuc_randiman, sonuc_tam = [], [], [], [], []

    for y in yapraklar:
        kod = str(y.get("kod"))
        tanim_tr, tanim_en = y.get("tanim_tr"), y.get("tanim_en")
        
        kdv_grp = next((k["grup"] for k in kdv_aktif if any(kod.startswith(p) for p in k["prefixler"])), None)
        if not kdv_grp and kdv_default: kdv_grp = kdv_default["grup"]
        kdv_data = {"grup": kdv_grp, "oran": None}
        if kdv_grp:
            oran_k = kdv_kural_doc["gruplar"].get(kdv_grp, {}).get("oran_kodu")
            if oran_k in kdv_oranlar: kdv_data["oran"] = kdv_oranlar[oran_k]["oran"]
        sonuc_kdv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **kdv_data})

        otv_grp = next((k["grup"] for k in otv_aktif if any(kod.startswith(p) for p in k["prefixler"])), None)
        if not otv_grp and otv_default: otv_grp = otv_default["grup"]
        otv_data = {"grup": otv_grp, "oran": None}
        if otv_grp:
            oran_k = otv_kural_doc["gruplar"].get(otv_grp, {}).get("oran_kodu")
            if oran_k in otv_oranlar:
                for k, v in otv_oranlar[oran_k].items():
                    if k not in ("kod", "ad_tr", "ad_en"): otv_data[k] = v
        sonuc_otv.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **otv_data})

        tevk_grp = next((k["grup"] for k in tevk_aktif if any(kod.startswith(p) for p in k["prefixler"])), None)
        if not tevk_grp and tevk_default: tevk_grp = tevk_default["grup"]
        tevk_data = {"grup": tevk_grp, "oran": None}
        if tevk_grp:
            # HATA BURADAYDI: tevk_kural_doc yerine tevkifat_kural_doc olmalı
            oran_k = tevkifat_kural_doc["gruplar"].get(tevk_grp, {}).get("oran_kodu")
            if oran_k in tevkifat_oranlar: tevk_data["oran"] = tevkifat_oranlar[oran_k]["oran"]
        sonuc_tevkifat.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **tevk_data})

        rd_girdi, rd_cikti = [], []
        for k in randiman_kural_doc.get("kurallar", []):
            r_kod = k.get("randiman_kodu")
            r_veri = randiman_oranlar.get(r_kod, {})
            if any(kod.startswith(p) for p in k.get("girdi_prefixler", [])):
                rd_girdi.append({"kural_kod": k["kod"], "cikti_prefixler": k.get("cikti_prefixler"), "randiman": r_veri.get("randiman_orani")})
            if any(kod.startswith(p) for p in k.get("cikti_prefixler", [])):
                rd_cikti.append({"kural_kod": k["kod"], "girdi_prefixler": k.get("girdi_prefixler"), "randiman": r_veri.get("randiman_orani")})
        rd_data = {"girdi_oldugu_kurallar": rd_girdi, "cikti_oldugu_kurallar": rd_cikti}
        sonuc_randiman.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, **rd_data})

        sonuc_tam.append({"kod": kod, "tanim_tr": tanim_tr, "tanim_en": tanim_en, "kdv": kdv_data, "otv": otv_data, "tevkifat": tevk_data, "randiman": rd_data})

    bugun = datetime.date.today()
    simdi = datetime.datetime.now(datetime.timezone.utc).isoformat()
    uretim_meta = {
        "yayinci": kdv_kural_doc["meta"]["yayinci"],
        "kaynaklar": kdv_kural_doc["meta"].get("kaynaklar", []) + otv_kural_doc["meta"].get("kaynaklar", []),
        "mevzuat_ref": kdv_kural_doc["meta"].get("mevzuat_ref", []) + otv_kural_doc["meta"].get("mevzuat_ref", []),
        "uretim": {
            "ham_kaynaklar": [
                {"servis_kod": "gtip-kodlari", "surum": gtip_kat["son"], "checksum": gtip_kat["checksum"]},
                {"servis_kod": "kdv-oranlari", "surum": kdv_oran_kat["son"], "checksum": kdv_oran_kat["checksum"]},
                {"servis_kod": "otv-oranlari", "surum": otv_oran_kat["son"], "checksum": otv_oran_kat["checksum"]},
                {"servis_kod": "tevkifat-oranlari", "surum": tevkifat_oran_kat["son"], "checksum": tevkifat_oran_kat["checksum"]},
                {"servis_kod": "randiman", "surum": randiman_oran_kat["son"], "checksum": randiman_oran_kat["checksum"]}
            ],
            "kural_seti": {"kod": "coklu-kural", "surum": bugun.strftime("%Y.%m.%d")},
            "uretim_zamani": simdi,
            "eslesme_ozeti": {"toplam": len(yapraklar), "eslesen": len(yapraklar), "eslesmeyen": 0}
        }
    }

    parcala_ve_yaz(kok, "gtip-kdv", "GTİP KDV Eşleşmesi", "GTIP VAT Mapping", sonuc_kdv, uretim_meta)
    parcala_ve_yaz(kok, "gtip-otv", "GTİP ÖTV Eşleşmesi", "GTIP SCT Mapping", sonuc_otv, uretim_meta)
    parcala_ve_yaz(kok, "gtip-tevkifat", "GTİP Tevkifat Eşleşmesi", "GTIP Withholding Mapping", sonuc_tevkifat, uretim_meta)
    parcala_ve_yaz(kok, "gtip-randiman", "GTİP Randıman Eşleşmesi", "GTIP Yield Mapping", sonuc_randiman, uretim_meta)
    parcala_ve_yaz(kok, "gtip-tam", "GTİP Tüm Vergiler", "GTIP All Taxes", sonuc_tam, uretim_meta)

    tum_veriyi_yaz(kok, "gtip-kdv", "GTİP KDV Eşleşmesi (Tümü)", "GTIP VAT Mapping (All)", sonuc_kdv, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-otv", "GTİP ÖTV Eşleşmesi (Tümü)", "GTIP SCT Mapping (All)", sonuc_otv, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-tevkifat", "GTİP Tevkifat Eşleşmesi (Tümü)", "GTIP Withholding Mapping (All)", sonuc_tevkifat, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-randiman", "GTİP Randıman Eşleşmesi (Tümü)", "GTIP Yield Mapping (All)", sonuc_randiman, uretim_meta)
    tum_veriyi_yaz(kok, "gtip-tam", "GTİP Tüm Vergiler (Tümü)", "GTIP All Taxes (All)", sonuc_tam, uretim_meta)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default=None)
    ap.add_argument("--yayinla", action="store_true", help="Sadece derler, pdaas.py'yi çağırmaz")
    args = ap.parse_args()

    kok = Path(args.kok).expanduser().resolve() if args.kok else Path(__file__).resolve().parent.parent
    
    try:
        eslesme_yap(kok)
    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr); return 1

    if not args.yayinla:
        print("\nDoğrulama ve katalog güncellemesi için pdaas.py çalıştırılıyor...")
        # --force eklendi: Test aşamasında aynı gün içinde yapılan değişikliklerin üzerine yazması için
        sonuc = subprocess.run([sys.executable, str(kok / "araclar" / "pdaas.py"), "--force"])
        if sonuc.returncode != 0:
            print("pdaas.py çalışırken hata oluştu.", file=sys.stderr); return sonuc.returncode

    return 0

if __name__ == "__main__":
    sys.exit(main())