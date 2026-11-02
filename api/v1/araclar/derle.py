#!/usr/bin/env python3
"""Düz API klasöründen GTİP, CPC, NACE ve ISCO konsolide kartları üretir."""
import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


HAM = {
    "gtip": "gtip-kodlari.json", "cpc": "cpc-kodlari.json",
    "nace": "nace-kodlari.json", "isco": "isco-kodlari.json",
    "sgk_meslek": "sgk-meslek-kodlari.json",
    "tesvik": "sgk-tesvik-kodlari.json",
    "mesleki_belgeler": "mesleki-belgeler.json",
    "faaliyet_belgeleri": "faaliyet-belgeleri.json",
    "kdv": "kdv.json", "otv": "otv.json", "tevkifat": "tevkifat.json",
    "gumruk": "gumruk-vergisi.json",
    "randiman": "randiman.json", "belgeler": "zorunlu-belgeler.json",
}
KURALLAR = {
    "vergi": "vergi-kurallari.json", "randiman": "randiman-kurallar.json",
    "belgeler": "belge-kurallari.json",
    "siniflama": "siniflama-kurallar.json",
    "tesvik": "tesvik-kurallari.json",
}
GORUNUM_DOSYASI = "gtip-gorunum-kurallar.json"
ISLEMLER = ("yurtici", "ithalat", "ihracat")
KIMLIK = ("kod", "ust_kod", "seviye", "seviye_adi", "sira", "yaprak", "ad_tr", "ad_en")
SERVIS_ADI = {"tr": "GTİP Konsolide Ürün Kartları", "en": "Consolidated GTIP Product Cards"}
CPC_SERVIS_ADI = {"tr": "CPC Konsolide Ürün ve Hizmet Kartları", "en": "Consolidated CPC Product and Service Cards"}
NACE_SERVIS_ADI = {"tr": "NACE Konsolide Faaliyet Kartları", "en": "Consolidated NACE Activity Cards"}
ISCO_SERVIS_ADI = {"tr": "ISCO Konsolide Meslek Kartları", "en": "Consolidated ISCO Occupation Cards"}
ESKI_SERVISLER = {"gtip-tam", "gtip-kdv", "gtip-otv", "gtip-tevkifat", "gtip-randiman",
                  "kdv-kurallar", "otv-kurallar", "tevkifat-kurallar",
                  "cpc-gtip", "cpc-gtip-konsolide", "nace-gtip", "nace-cpc",
                  "zorunlu-belgeler-kurallar", "mesleki-belgeler-kurallar",
                  "faaliyet-belgeleri-kurallar"}
SURUM = "1.0.0"
API_YOLU = "/api/v1"
VERI_DOSYALARI = (tuple(ad for tur, ad in HAM.items() if tur not in ("isco", "sgk_meslek", "tesvik", "mesleki_belgeler", "faaliyet_belgeleri"))
                  + tuple(ad for tur, ad in KURALLAR.items() if tur != "tesvik"))


def oku(yol):
    if not yol.is_file():
        raise FileNotFoundError(f"Gerekli kaynak dosya yok: {yol}")
    with yol.open(encoding="utf-8-sig") as f:
        d = json.load(f)
    if not isinstance(d, dict) or not isinstance(d.get("meta"), dict):
        raise ValueError(f"meta nesnesi bulunamadı: {yol}")
    return d


def belge_kural_bolumleri(d):
    """Tek belge kural dosyasındaki üç ilişki türünü ve toplamlarını doğrular."""
    bolumler = {
        "urun_kurallari": "urun_kural_sayisi",
        "faaliyet_kurallari": "faaliyet_kural_sayisi",
        "meslek_kurallari": "meslek_kural_sayisi",
    }
    yapi = d["meta"].get("yapi", {})
    gorulen = set()
    toplam = 0
    sonuc = {}
    for alan, sayac_alani in bolumler.items():
        kayitlar = d.get(alan)
        if not isinstance(kayitlar, list):
            raise ValueError(f"belge-kurallari.json: {alan} dizi olmalı")
        if yapi.get(sayac_alani) != len(kayitlar):
            raise ValueError(f"belge-kurallari.json: {sayac_alani} tutarsız")
        for r in kayitlar:
            kod = r.get("kod") if isinstance(r, dict) else None
            if not isinstance(kod, str) or not kod or kod in gorulen:
                raise ValueError(f"belge-kurallari.json: mükerrer/boş kural kodu: {kod}")
            gorulen.add(kod)
        sonuc[alan] = kayitlar
        toplam += len(kayitlar)
    if yapi.get("kayit_sayisi") != toplam:
        raise ValueError("belge-kurallari.json: toplam kayit_sayisi tutarsız")
    return sonuc


def varsa_oku(yol):
    if not yol.is_file():
        return None
    with yol.open(encoding="utf-8-sig") as f:
        return json.load(f)


def yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")


def kanonik(d):
    return json.dumps(d, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha_nesne(d):
    return "sha256:" + hashlib.sha256(kanonik(d)).hexdigest()


def sha_dosya(yol):
    h = hashlib.sha256()
    with yol.open("rb") as f:
        for parca in iter(lambda: f.read(1024 * 1024), b""):
            h.update(parca)
    return "sha256:" + h.hexdigest()


def icerik(d):
    return {alan: deger for alan, deger in d.items() if alan != "meta"}


def kayit_adi(r, dil):
    return r.get("ad_" + dil) or r.get("tanim_" + dil)


def kimlik_karti(r):
    kart = {alan: r[alan] for alan in KIMLIK if alan not in ("ad_tr", "ad_en") and r.get(alan) is not None}
    kart["ad_tr"] = kayit_adi(r, "tr")
    kart["ad_en"] = kayit_adi(r, "en")
    if r.get("yaprak") and "olcu_birimi" in r:
        kart["olcu_birimi"] = r["olcu_birimi"]
    return kart


def isco_sgk_kartlari(isco_ham, sgk_ham):
    """Altı haneli SGK kodlarını dört haneli ISCO gruplarına bağlar.

    Yalnızca açıkça otomatik kullanıma onaylı kayıtlar doğrulanmış sayılır.
    Onaysız fakat biçimi ve grubu uygun kayıtlar ayrı aday alanında tutulur.
    """
    isco = isco_ham.get("kayitlar", [])
    sgk = sgk_ham.get("kayitlar", [])
    if not isco or not isinstance(sgk, list):
        raise ValueError("ISCO veya SGK meslek kayıtları eksik")
    kodlar = [str(r["kod"]) for r in isco]
    if len(kodlar) != len(set(kodlar)):
        raise ValueError("isco-kodlari.json: mükerrer ISCO kodu")
    dort_haneliler = {kod for kod in kodlar if re.fullmatch(r"\d{4}", kod)}
    dogrulanan = defaultdict(list)
    aday = defaultdict(list)
    sayac = Counter()
    gorulen_sgk = set()
    for r in sgk:
        kod = str(r.get("kod", ""))
        if not re.fullmatch(r"\d{4}\.\d{2}", kod):
            sayac["gecersiz_kod_bicimi"] += 1
            continue
        if kod in gorulen_sgk:
            raise ValueError(f"sgk-meslek-kodlari.json: mükerrer kod: {kod}")
        gorulen_sgk.add(kod)
        grup = kod[:4]
        if grup not in dort_haneliler:
            sayac["isco_grubu_bulunamadi"] += 1
            continue
        ad_tr, ad_en = kayit_adi(r, "tr"), kayit_adi(r, "en")
        if not ad_tr or not ad_en:
            sayac["adi_eksik"] += 1
            continue
        ozet = {"kod": kod, "ad_tr": ad_tr, "ad_en": ad_en}
        if r.get("otomatik_kullan") is True:
            dogrulanan[grup].append(ozet)
            sayac["dogrulanan"] += 1
        else:
            aday[grup].append(ozet)
            sayac["aday"] += 1
    sonuc = []
    for r in isco:
        kod = str(r["kod"])
        item = {k: r[k] for k in ("ust_kod", "seviye", "yaprak") if r.get(k) is not None}
        item = {"kod": kod, **item, "ad_tr": kayit_adi(r, "tr"), "ad_en": kayit_adi(r, "en")}
        if not item["ad_tr"] or not item["ad_en"]:
            raise ValueError(f"isco-kodlari.json: adı eksik kayıt: {kod}")
        if dogrulanan.get(kod):
            item["sgk"] = sorted(dogrulanan[kod], key=lambda x: x["kod"])
        if aday.get(kod):
            item["sgk_adaylari"] = sorted(aday[kod], key=lambda x: x["kod"])
        sonuc.append(item)
    sayac["dogrulanan_isco_grubu"] = len(dogrulanan)
    sayac["adayli_isco_grubu"] = len(aday)
    return sonuc, sayac


def isco_mesleki_belge_baglantilari(isco_ham, belge_ham, kurallar):
    """Meslek belgelerini sadece açıkça eşleştirilmiş dört haneli ISCO'ya ekler.

    Meslek grubundaki herkes için MYK/SRC zorunluluğu varsayılmaz: koşullu
    bağlantının gerekçesi ve istisnaları kullanıcı kartında taşınır.
    """
    isco = {str(r["kod"]): r for r in isco_ham["kayitlar"]}
    kayitlar = belge_ham.get("kayitlar", [])
    if not isinstance(kayitlar, list) or not isinstance(kurallar, list):
        raise ValueError("Mesleki belgeler ve kurallar dizi biçiminde olmalı")
    belgeler = {}
    kaynaklar = {r.get("kod") for r in belge_ham.get("meta", {}).get("kaynaklar", {}).get("referanslar", [])}
    for r in kayitlar:
        kod = r.get("kod")
        if not isinstance(kod, str) or not kod or kod in belgeler:
            raise ValueError(f"mesleki-belgeler.json: geçersiz/mükerrer kod: {kod}")
        if not all(isinstance(r.get(k), str) and r[k].strip() for k in ("ad_tr", "ad_en", "tur")):
            raise ValueError(f"mesleki-belgeler.json: belge alanları eksik: {kod}")
        if r.get("kaynak_ref") not in kaynaklar:
            raise ValueError(f"mesleki-belgeler.json: resmî kaynak bulunamadı: {kod}")
        belgeler[kod] = r
    if belge_ham["meta"]["yapi"]["kayit_sayisi"] != len(belgeler):
        raise ValueError("mesleki-belgeler.json: kayit_sayisi tutarsız")
    sonuc = defaultdict(list)
    gorulen_kurallar = set()
    gorulen_iliski = set()
    sayac = Counter()
    for r in kurallar:
        kural_kodu = r.get("kod")
        if not isinstance(kural_kodu, str) or not kural_kodu or kural_kodu in gorulen_kurallar:
            raise ValueError(f"belge-kurallari.json/meslek_kurallari: mükerrer/boş kural: {kural_kodu}")
        gorulen_kurallar.add(kural_kodu)
        belge = belgeler.get(r.get("belge_ref"))
        if belge is None:
            raise ValueError(f"{kural_kodu}: mesleki-belgeler.json içinde bulunmayan belge_ref")
        durum = r.get("durum")
        if durum not in ("zorunlu", "kosullu"):
            raise ValueError(f"{kural_kodu}: durum zorunlu/kosullu olmalı")
        kosul = r.get("kosul")
        if durum == "kosullu" and not (isinstance(kosul, dict) and
                all(isinstance(kosul.get(d), str) and kosul[d].strip() for d in ("tr", "en"))):
            raise ValueError(f"{kural_kodu}: koşullu belge için Türkçe/İngilizce koşul gerekli")
        kodlar = r.get("isco_kodlari")
        if not isinstance(kodlar, list) or not kodlar:
            raise ValueError(f"{kural_kodu}: isco_kodlari boş")
        for isco_kodu in kodlar:
            if not isinstance(isco_kodu, str) or not re.fullmatch(r"\d{4}", isco_kodu) or isco_kodu not in isco:
                raise ValueError(f"{kural_kodu}: bilinmeyen dört haneli ISCO: {isco_kodu}")
            iliski = (isco_kodu, belge["kod"])
            if iliski in gorulen_iliski:
                raise ValueError(f"{kural_kodu}: mükerrer ISCO–meslek belgesi bağı: {iliski}")
            gorulen_iliski.add(iliski)
            kart = {"kod": belge["kod"], "ad_tr": belge["ad_tr"], "ad_en": belge["ad_en"],
                    "tur": belge["tur"], "durum": durum, "kaynak_ref": belge["kaynak_ref"]}
            if kosul is not None:
                kart["kosul"] = kosul
            sonuc[isco_kodu].append(kart)
            sayac[durum] += 1
    sayac["kural"] = len(kurallar)
    sayac["belge"] = len(belgeler)
    sayac["iliski"] = len(gorulen_iliski)
    sayac["meslek"] = len(sonuc)
    return dict(sonuc), sayac


def isco_nace_baglantilari(isco_ham, nace_ham, siniflama_kurallari):
    """ISCO meslekleri ile muhtemel NACE faaliyetleri arasında çift yönlü bağlantı kurar."""
    isco_sozluk = {str(r["kod"]): r for r in isco_ham["kayitlar"]}
    nace_sozluk = {str(r["kod"]): r for r in nace_ham["kayitlar"]}
    kurallar = siniflama_kurallari.get("isco_nace_kurallari", [])
    if not isinstance(kurallar, list):
        raise ValueError("siniflama-kurallar.json: isco_nace_kurallari dizi olmalı")
    isco_to_nace = defaultdict(dict)
    nace_to_isco = defaultdict(dict)
    gorulen_kurallar = set()
    for r in kurallar:
        kural_kodu = r.get("kod")
        if not isinstance(kural_kodu, str) or kural_kodu in gorulen_kurallar:
            raise ValueError(f"Mükerrer veya boş ISCO–NACE kural kodu: {kural_kodu}")
        gorulen_kurallar.add(kural_kodu)
        isco_kodu = str(r.get("isco_kodu", ""))
        if not re.fullmatch(r"\d{4}", isco_kodu) or isco_kodu not in isco_sozluk:
            raise ValueError(f"{kural_kodu}: bilinmeyen dört haneli ISCO kodu: {isco_kodu}")
        nace_kodlari = r.get("nace_kodlari")
        if not isinstance(nace_kodlari, list) or not nace_kodlari:
            raise ValueError(f"{kural_kodu}: NACE kodları boş")
        meslek = isco_sozluk[isco_kodu]
        for nace_kodu in nace_kodlari:
            if not isinstance(nace_kodu, str) or not re.fullmatch(r"\d{2}\.\d{2}", nace_kodu) or nace_kodu not in nace_sozluk:
                raise ValueError(f"{kural_kodu}: bilinmeyen dört basamaklı NACE kodu: {nace_kodu}")
            if nace_kodu in isco_to_nace[isco_kodu]:
                raise ValueError(f"Yinelenen ISCO–NACE bağlantısı: {isco_kodu}/{nace_kodu}")
            faaliyet = nace_sozluk[nace_kodu]
            isco_to_nace[isco_kodu][nace_kodu] = {
                "kod": nace_kodu, "ad_tr": kayit_adi(faaliyet, "tr"),
                "ad_en": kayit_adi(faaliyet, "en")}
            nace_to_isco[nace_kodu][isco_kodu] = {
                "kod": isco_kodu, "ad_tr": kayit_adi(meslek, "tr"),
                "ad_en": kayit_adi(meslek, "en")}
    sayac = {"kural": len(kurallar),
             "iliski": sum(map(len, isco_to_nace.values())),
             "isco_grubu": len(isco_to_nace), "nace_faaliyeti": len(nace_to_isco)}
    return ({k: [v[code] for code in sorted(v)] for k, v in isco_to_nace.items()},
            {k: [v[code] for code in sorted(v)] for k, v in nace_to_isco.items()},
            sayac)


def nace_tesvik_adaylari(nace_ham, tesvik_ham, tesvik_kurallari):
    """Faaliyet kodundan yalnızca koşullu SGK teşvik adaylarını üretir."""
    nace = {str(r["kod"]): r for r in nace_ham["kayitlar"]}
    tesvik = {str(r["kod"]): r for r in tesvik_ham["kayitlar"]}
    if len(tesvik) != len(tesvik_ham["kayitlar"]):
        raise ValueError("sgk-tesvik-kodlari.json: mükerrer kod")
    kurallar = tesvik_kurallari.get("kurallar", [])
    if not isinstance(kurallar, list):
        raise ValueError("tesvik-kurallari.json: kurallar dizi olmalı")
    kural_kodlari = set()
    for r in kurallar:
        kod = r.get("kod")
        ref = r.get("tesvik_ref")
        if not isinstance(kod, str) or kod in kural_kodlari:
            raise ValueError(f"tesvik-kurallari.json: mükerrer/boş kural: {kod}")
        kural_kodlari.add(kod)
        if ref not in tesvik:
            raise ValueError(f"{kod}: bulunmayan SGK teşvik kodu: {ref}")
        if not r.get("nace_bolumleri") and not r.get("nace_prefixler"):
            raise ValueError(f"{kod}: NACE kapsamı boş")
        puan_anahtari = r.get("puan_anahtari")
        if puan_anahtari and puan_anahtari not in tesvik[ref].get("puan", {}):
            raise ValueError(f"{kod}: kaynak teşvikte tanımsız puan: {puan_anahtari}")

    bolum_onbellek = {}

    def bolum_bul(kod, iz=None):
        if kod in bolum_onbellek:
            return bolum_onbellek[kod]
        if iz is None:
            iz = set()
        if kod in iz:
            raise ValueError(f"NACE üst kod zincirinde döngü: {kod}")
        iz.add(kod)
        r = nace[kod]
        ust = r.get("ust_kod")
        if re.fullmatch(r"[A-Z]", kod):
            sonuc = kod
        elif ust is not None and str(ust) in nace:
            sonuc = bolum_bul(str(ust), iz)
        else:
            raise ValueError(f"NACE kaydının bölüm kodu çözülemedi: {kod}")
        iz.remove(kod)
        bolum_onbellek[kod] = sonuc
        return sonuc

    sonuc = {}
    sayac = Counter()
    for nace_kodu in nace:
        bolum = bolum_bul(nace_kodu)
        ref_secimleri = {}
        for r in kurallar:
            bolumler = r.get("nace_bolumleri", [])
            prefixler = r.get("nace_prefixler", [])
            if not ("*" in bolumler or bolum in bolumler or
                    any(nace_kodu.startswith(prefix) for prefix in prefixler)):
                continue
            ref = r["tesvik_ref"]
            onceki = ref_secimleri.get(ref)
            oncelik = r.get("oncelik", 0)
            if onceki is None or oncelik > onceki.get("oncelik", 0):
                ref_secimleri[ref] = r
        if not ref_secimleri:
            continue
        adaylar = []
        for ref in sorted(ref_secimleri):
            r = ref_secimleri[ref]
            kaynak = tesvik[ref]
            aday = {"kod": ref, "ad_tr": kayit_adi(kaynak, "tr"),
                    "ad_en": kayit_adi(kaynak, "en"), "durum": "kosullu"}
            puan_anahtari = r.get("puan_anahtari")
            if puan_anahtari:
                aday["puan"] = kaynak["puan"][puan_anahtari]
            adaylar.append(aday)
        sonuc[nace_kodu] = adaylar
        sayac["aday_iliski_sayisi"] += len(adaylar)
        sayac["eslesen_nace_kayit_sayisi"] += 1
    sayac["kural_sayisi"] = len(kurallar)
    return sonuc, sayac


def nace_faaliyet_belgeleri(nace_ham, belge_ham, kurallar):
    """İşletme belgelerini koşullu NACE yapraklarına bağlar; ürün belgeleriyle karıştırmaz."""
    kayitlar = belge_ham.get("kayitlar", [])
    if not isinstance(kayitlar, list) or not isinstance(kurallar, list):
        raise ValueError("Faaliyet belgeleri ve kuralları dizi olmalı")
    kaynaklar = {r.get("kod") for r in belge_ham["meta"].get("kaynaklar", {}).get("referanslar", [])}
    belgeler = {}
    for r in kayitlar:
        kod = r.get("kod")
        if not isinstance(kod, str) or not kod or kod in belgeler:
            raise ValueError(f"faaliyet-belgeleri.json: boş/mükerrer belge kodu: {kod}")
        if any(not isinstance(r.get(k), str) or not r[k].strip()
               for k in ("ad_tr", "ad_en", "tur", "kaynak_ref")):
            raise ValueError(f"faaliyet-belgeleri.json: alanları eksik: {kod}")
        if r["kaynak_ref"] not in kaynaklar:
            raise ValueError(f"faaliyet-belgeleri.json: resmî kaynak referansı bulunamadı: {kod}")
        belgeler[kod] = r
    if belge_ham["meta"]["yapi"]["kayit_sayisi"] != len(belgeler):
        raise ValueError("faaliyet-belgeleri.json: kayit_sayisi tutarsız")
    kural_kodlari = set()
    for r in kurallar:
        kod = r.get("kod")
        if not isinstance(kod, str) or not kod or kod in kural_kodlari:
            raise ValueError(f"belge-kurallari.json/faaliyet_kurallari: mükerrer/boş kural: {kod}")
        kural_kodlari.add(kod)
        if r.get("belge_ref") not in belgeler:
            raise ValueError(f"{kod}: tanımsız faaliyet belgesi referansı: {r.get('belge_ref')}")
        if r.get("durum") != "kosullu":
            raise ValueError(f"{kod}: yalnızca koşulu açıkça belirtilmiş eşleştirmeler kullanılabilir")
        kosul = r.get("kosul")
        if not isinstance(kosul, dict) or any(not isinstance(kosul.get(d), str) or not kosul[d].strip()
                                              for d in ("tr", "en")):
            raise ValueError(f"{kod}: iki dilli koşul zorunludur")
        prefixler = r.get("nace_prefixler")
        haricler = r.get("haric_nace_prefixler", [])
        if not isinstance(prefixler, list) or not prefixler or any(not isinstance(p, str) or not p for p in prefixler):
            raise ValueError(f"{kod}: nace_prefixler geçersiz")
        if not isinstance(haricler, list) or any(not isinstance(p, str) or not p for p in haricler):
            raise ValueError(f"{kod}: haric_nace_prefixler geçersiz")
    sonuc = {}
    sayac = Counter()
    for r in nace_ham["kayitlar"]:
        # Hiyerarşik üst kodlarda işletme kurulamayacağından bu alana belge atanmaz.
        if not r.get("yaprak"):
            continue
        nace_kodu = str(r["kod"])
        baglar = {}
        for kural in kurallar:
            prefixler = kural["nace_prefixler"]
            if not any(p == "*" or nace_kodu.startswith(p) for p in prefixler):
                continue
            if any(nace_kodu.startswith(p) for p in kural.get("haric_nace_prefixler", [])):
                continue
            kaynak = belgeler[kural["belge_ref"]]
            belge_kodu = kaynak["kod"]
            if belge_kodu in baglar:
                raise ValueError(f"{nace_kodu}: tekrarlanan faaliyet belgesi: {belge_kodu}")
            baglar[belge_kodu] = {"kod": belge_kodu, "ad_tr": kaynak["ad_tr"],
                                  "ad_en": kaynak["ad_en"], "tur": kaynak["tur"],
                                  "durum": "kosullu", "kaynak_ref": kaynak["kaynak_ref"],
                                  "kosul": kural["kosul"]}
        if baglar:
            sonuc[nace_kodu] = [baglar[k] for k in sorted(baglar)]
            sayac["eslesen_kayit"] += 1
            sayac["iliski"] += len(baglar)
    sayac["belge"] = len(belgeler)
    sayac["kural"] = len(kurallar)
    return sonuc, sayac


def iliskisel_kart_ozeti(gtip_kodlari, gtip_kartlari, diger_sinif, uygulama_bilgileri=True):
    """CPC için GTİP uygulamalarını, NACE için yalnız ilişkili sınıfları özetler."""
    urunler = []
    siniflar = {}
    vergiler = {}
    belgeler = {}
    randimanlar = []
    for kod in sorted(gtip_kodlari):
        kart = gtip_kartlari.get(kod)
        if kart is None or not kart.get("urun_karti"):
            raise ValueError(f"Konsolide sınıflama bağlantısında bulunamayan ürün kartı: {kod}")
        urunler.append({"kod": kod, "ad_tr": kart["ad_tr"], "ad_en": kart["ad_en"]})
        for es in kart.get(diger_sinif, []):
            siniflar[es["kod"]] = {"kod": es["kod"], "ad_tr": es["ad_tr"], "ad_en": es["ad_en"]}
        if uygulama_bilgileri:
            for islem in ISLEMLER:
                for tur, veri in kart.get("vergi", {}).get(islem, {}).items():
                    anahtar = kanonik(veri)
                    grup = vergiler.setdefault(islem, {}).setdefault(tur, {}).setdefault(
                        anahtar, {**veri, "gtip_kodlari": []})
                    grup["gtip_kodlari"].append(kod)
                for belge in kart.get("belgeler", {}).get(islem, []):
                    anahtar = kanonik(belge)
                    grup = belgeler.setdefault(islem, {}).setdefault(
                        anahtar, {**belge, "gtip_kodlari": []})
                    grup["gtip_kodlari"].append(kod)
            if kart.get("randiman"):
                randimanlar.append({"gtip_kodu": kod, "surecler": kart["randiman"]})
    sonuc = {"gtip": urunler}
    if siniflar:
        sonuc[diger_sinif] = [siniflar[k] for k in sorted(siniflar)]
    if vergiler:
        sonuc["vergi"] = {
            islem: {tur: sorted(gruplar.values(), key=lambda x: (str(x.get("ref", "")), kanonik(x)))
                    for tur, gruplar in sorted(vergiler[islem].items())}
            for islem in ISLEMLER if islem in vergiler
        }
    if belgeler:
        sonuc["belgeler"] = {
            islem: sorted(belgeler[islem].values(), key=lambda x: (str(x.get("kod", "")), kanonik(x)))
            for islem in ISLEMLER if islem in belgeler
        }
    if randimanlar:
        sonuc["randiman"] = randimanlar
    return sonuc


def gorunum_haric_kodlari(kural_dosyasi, gtip_kayitlari):
    if kural_dosyasi is None:
        return set()
    yaprak_kodlari = {str(r["kod"]) for r in gtip_kayitlari if r.get("yaprak")}
    haric = set()
    if kural_dosyasi.get("meta", {}).get("yapi", {}).get("tip") != "kural-seti":
        raise ValueError(f"{GORUNUM_DOSYASI}: meta.yapi.tip kural-seti olmalı")
    for kural in kural_dosyasi.get("kurallar", []):
        if kural.get("islem") != "urun_kartinda_gosterme":
            raise ValueError(f"Bilinmeyen GTİP görünüm işlemi: {kural.get('islem')}")
        for kod in kural.get("gtip_kodlari", []):
            if not isinstance(kod, str) or len(kod) != 12 or not kod.isdecimal() or kod not in yaprak_kodlari:
                raise ValueError(f"Görünüm kuralında geçersiz 12 haneli yaprak GTİP: {kod}")
            if kod in haric:
                raise ValueError(f"Görünüm kurallarında mükerrer GTİP: {kod}")
            haric.add(kod)
    return haric


class PrefixIndex:
    def __init__(self, kurallar, alan, geneller=()):
        self.by_prefix = defaultdict(list)
        self.genel = []
        self.alan = alan
        for r in kurallar:
            prefixler = [str(v) for v in r.get(alan, []) if str(v)]
            if prefixler:
                for p in prefixler:
                    self.by_prefix[p].append(r)
            elif r.get("kod") in geneller:
                self.genel.append(r)

    def bul(self, kod):
        bulunan = {r["kod"]: r for r in self.genel}
        for uzunluk in range(1, len(kod) + 1):
            for r in self.by_prefix.get(kod[:uzunluk], ()):
                bulunan[r["kod"]] = r
        eslesen = (r for r in bulunan.values() if not any(kod.startswith(str(p)) for p in r.get("haric_gtip_prefixler", ())))
        return sorted(eslesen, key=lambda r: (-max((len(str(p)) for p in r.get(self.alan, []) if kod.startswith(str(p))), default=0), -r.get("oncelik", 0), r["kod"]))


class KayitYazici:
    def __init__(self, yol):
        self.yol = yol
        self.dosya = yol.open("w", encoding="utf-8")
        self.hash = hashlib.sha256(b"[")
        self.adet = 0

    def ekle(self, nesne):
        metin = kanonik(nesne)
        if self.adet:
            self.hash.update(b",")
        self.hash.update(metin)
        self.dosya.write(json.dumps(nesne, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.adet += 1

    def bitir(self):
        self.dosya.close()
        self.hash.update(b"]")
        return "sha256:" + self.hash.hexdigest()


class VergiIndex:
    """Ham vergi kayıtlarından izlenebilir, sayısal örnek ürün kartları üretir."""

    def __init__(self, kurallar, ham, tarih):
        self.ham = ham
        self.tarih = tarih
        self.kurallar = {r["kod"]: r for r in kurallar}
        if len(self.kurallar) != len(kurallar):
            raise ValueError("vergi-kurallari.json: mükerrer kural kodu")
        self.gtip = PrefixIndex([
            {**r, "gtip_prefixler": r.get("eslesme", {}).get("gtip_prefix", [])}
            for r in kurallar
        ], "gtip_prefixler")
        self.cpc = PrefixIndex([
            {**r, "cpc_prefixler": r.get("eslesme", {}).get("cpc_prefix", [])}
            for r in kurallar
        ], "cpc_prefixler")
        self.tam = defaultdict(list)
        self.kullanilan = set()
        self.ref_indeks = {}
        for r in kurallar:
            eslesme = r.get("eslesme", {})
            tam_kod = eslesme.get("gtip")
            if tam_kod and tam_kod != "$gtip":
                self.tam[tam_kod].append(r)
            ref = r["ref"]
            dosya = ref["dosya"]
            kaynak = ham.get(dosya)
            if kaynak is None:
                raise ValueError(f"{r['kod']}: ham vergi kaynağı bulunamadı: {dosya}")
            koleksiyon = kaynak
            for alan in ref["bolum"].split("."):
                koleksiyon = koleksiyon[alan]
            if not isinstance(koleksiyon, list):
                raise ValueError(f"{r['kod']}: geçersiz referans bölümü")
            anahtar = (dosya, ref["bolum"])
            if anahtar not in self.ref_indeks:
                by_code = defaultdict(list)
                by_gtp = defaultdict(list)
                for kayit in koleksiyon:
                    if kayit.get("kod") is not None:
                        by_code[str(kayit["kod"])].append(kayit)
                    gtp = kayit.get("gtp")
                    for prefix in ([gtp] if isinstance(gtp, str) else gtp or []):
                        if isinstance(prefix, str) and prefix:
                            by_gtp[prefix].append(kayit)
                self.ref_indeks[anahtar] = (by_code, by_gtp)
            if "kod" in ref and ref["kod"] not in self.ref_indeks[anahtar][0]:
                raise ValueError(f"{r['kod']}: ham vergi referansı yok: {ref['kod']}")

        gumruk = ham["gumruk-vergisi"]["ithalat"]
        self.gv = {r["kod"] for r in gumruk["kayitlar"]}
        self.igv = {r["kod"] for r in gumruk["ilave_vergiler"]}
        self.indirim_tam = {r["kod"] for r in gumruk["indirimler"] if r.get("kod")}
        self.indirim_prefix = set()
        for r in gumruk["indirimler"]:
            gtp = r.get("gtp")
            if isinstance(gtp, str):
                self.indirim_prefix.add(gtp)
            elif isinstance(gtp, list):
                self.indirim_prefix.update(p for p in gtp if isinstance(p, str))

        self.gumruk_sutunlari = ham["gumruk-vergisi"]["meta"]["tablo_haritasi"]["sutunlar"]

    def referans_kayitlari(self, kural, gtip):
        ref = kural["ref"]
        by_code, by_gtp = self.ref_indeks[(ref["dosya"], ref["bolum"])]
        if "kod" in ref:
            return by_code.get(ref["kod"], [])
        ara = ref.get("ara", {})
        if ara.get("kod") == "$gtip":
            return by_code.get(gtip, [])
        if ara.get("kod_veya_gtp") == "$gtip":
            bulunan = {id(k): k for k in by_code.get(gtip, [])}
            for uzunluk in range(1, len(gtip) + 1):
                for k in by_gtp.get(gtip[:uzunluk], []):
                    bulunan[id(k)] = k
            return list(bulunan.values())
        raise ValueError(f"{kural['kod']}: tanınmayan dinamik vergi referansı")

    def vergi_kaydi(self, kural, kaynak):
        sonuc = {"kural": kural["kod"], "durum": "kosullu"}
        for alan in ("kod", "ad_tr", "ad_en", "liste", "tur", "vergi_tipi",
                     "para_birimi", "birim", "alici_gruplari", "uygulama"):
            if kaynak.get(alan) is not None:
                sonuc[alan] = kaynak[alan]

        tarihce = kaynak.get("tarihce")
        if tarihce:
            aktif = next((x for x in tarihce if x["baslangic"] <= self.tarih
                          and (x.get("bitis") is None or self.tarih <= x["bitis"])), None)
            if aktif is None:
                return None  # Tarihi dışındaki vergi oranını yürürlükte gibi gösterme.
            for alan in ("oran", "tutar", "kesir"):
                if aktif.get(alan) is not None:
                    sonuc[alan] = aktif[alan]
        for alan in ("oran", "tutar", "kesir"):
            if alan not in sonuc and kaynak.get(alan) is not None:
                sonuc[alan] = kaynak[alan]
        if isinstance(sonuc.get("oran"), (float, int)):
            sonuc["oran_yuzde"] = round(sonuc["oran"] * 100, 8)

        for anahtar in ("gv", "igv"):
            oranlar = kaynak.get(anahtar)
            if isinstance(oranlar, list):
                liste = kaynak.get("liste")
                sutunlar = self.gumruk_sutunlari.get(liste)
                if not sutunlar or len(sutunlar) != len(oranlar):
                    raise ValueError(f"{kural['kod']}: {liste} gümrük sütunları ile oran sayısı uyuşmuyor")
                sonuc[anahtar + "_oranlari_yuzde"] = {
                    str(s): round(v * 100, 8) for s, v in zip(sutunlar, oranlar)
                    if isinstance(v, (float, int))
                }
                sonuc["durum"] = "menseye_bagli"
            elif isinstance(oranlar, (float, int)):
                sonuc[anahtar + "_oran_yuzde"] = round(oranlar * 100, 8)

        if kural["ref"]["bolum"].split(".")[-1] == "istisnalar":
            sonuc["istisna"] = True
        return sonuc

    @staticmethod
    def ornek_atama(tur, islem, adaylar):
        """Ham kayıtlardan tek bir örnek sonucu seçer; ayrıntılar kaynaklarda kalır."""
        if not adaylar:
            return None

        secilen = next((r for r in adaylar if r.get("istisna")), None) if tur == "kdv" else None
        if secilen is None:
            secilen = next((r for r in adaylar if "oran" in r or "tutar" in r), None)
        if secilen is None:
            secilen = adaylar[0]

        sonuc = {"ref": secilen["kural"]}

        if tur == "gumruk-vergisi" and islem == "ithalat":
            ana = next((r for r in adaylar if r["kural"] == "gumruk-ithalat-ana"), None)
            ilave = next((r for r in adaylar if r["kural"] == "gumruk-ithalat-ilave"), None)
            if ana is None and ilave is None:
                return {"ref": secilen["kural"], "durum": "ana_tarife_bilinmiyor"}
            ana_oranlari = (ana or {}).get("gv_oranlari_yuzde", {})
            ilave_oranlari = (ilave or {}).get("igv_oranlari_yuzde", {})
            ana_grup = next((g for g in ("du", "otdu", "7") if g in ana_oranlari), None)
            if ana_grup is None and ana_oranlari:
                ana_grup = list(ana_oranlari)[-1]
            ilave_grup = ana_grup if ana_grup in ilave_oranlari else next(
                (g for g in ("du", "otdu", "7") if g in ilave_oranlari), None)
            if ilave_grup is None and ilave_oranlari:
                ilave_grup = list(ilave_oranlari)[-1]
            gv = ana_oranlari.get(ana_grup) if ana_grup else (ana or {}).get("gv_oran_yuzde")
            igv = ilave_oranlari.get(ilave_grup) if ilave_grup else (ilave or {}).get("igv_oran_yuzde")
            if gv is not None or igv is not None:
                sonuc["ref"] = ana["kural"] if ana else ilave["kural"]
                sonuc["mense_varsayimi"] = (
                    "diger_ulkeler" if (ana_grup or ilave_grup) in ("du", "otdu")
                    else "son_tarife_sutunu"
                )
                if ana_grup:
                    sonuc["mense_grubu"] = ana_grup
                if ilave_grup and ilave_grup != ana_grup:
                    sonuc["igv_mense_grubu"] = ilave_grup
                if gv is not None and igv is not None:
                    sonuc["gv"] = round(gv / 100, 10)
                if igv is not None:
                    sonuc["igv"] = round(igv / 100, 10)
                    sonuc["igv_ref"] = ilave["kural"]
                sonuc["oran"] = round(((gv or 0) + (igv or 0)) / 100, 10)
                if gv is None:
                    sonuc["kapsam"] = "yalniz_igv"
                return sonuc
            return {"ref": sonuc["ref"], "durum": "oran_kaynakta_yok"}

        if secilen.get("istisna"):
            # İstisna sıfır oranlı tarife değildir.
            return {"istisna": True, "ref": secilen["kural"]}
        if tur == "gumruk-vergisi" and islem == "ihracat":
            return {"uygulama": secilen.get("uygulama", "kosullu"), "ref": secilen["kural"]}
        for alan in ("oran", "tutar", "birim", "para_birimi", "kesir"):
            if alan in secilen:
                sonuc[alan] = secilen[alan]
        if tur == "tevkifat" and "alici_gruplari" in secilen:
            sonuc["alici_gruplari"] = secilen["alici_gruplari"]
        if not any(alan in sonuc for alan in ("oran", "tutar")):
            sonuc["durum"] = "oran_kaynakta_yok"
        return sonuc

    def bul(self, kod, cpc_kodlari):
        secilen = {}

        def ekle(r, uzunluk=0):
            if r is not None:
                onceki = secilen.get(r["kod"])
                if onceki is None or uzunluk > onceki[1]:
                    secilen[r["kod"]] = (r, uzunluk)

        for r in self.tam.get(kod, ()):
            ekle(r, 100)
        for r in self.gtip.bul(kod):
            ekle(r, max((len(p) for p in r["gtip_prefixler"] if kod.startswith(p)), default=0))
        for cpc in cpc_kodlari:
            for r in self.cpc.bul(cpc):
                eslesme = r.get("eslesme", {})
                if eslesme.get("gtip_prefix") or eslesme.get("gtip"):
                    continue  # CPC, GTİP koşulunu tek başına geçersiz kılamaz.
                ekle(r, max((len(p) for p in r["cpc_prefixler"] if cpc.startswith(p)), default=0))

        for kural_kodu in ("kdv-genel-20", "kdv-ihracat-11-12", "gumruk-ihr-gv-genel"):
            ekle(self.kurallar.get(kural_kodu))
        for kural_kodu, uygun in (
            ("gumruk-ithalat-ana", kod in self.gv),
            ("gumruk-ithalat-ilave", kod in self.igv),
            ("gumruk-ithalat-indirim", kod in self.indirim_tam or any(kod.startswith(p) for p in self.indirim_prefix)),
        ):
            if uygun:
                ekle(self.kurallar.get(kural_kodu), 100)
        if any(r["tur"] == "otv" for r, _ in secilen.values()):
            ekle(self.kurallar.get("otv-ihracat-istisnasi"))

        sonuc = {}
        for islem in ISLEMLER:
            gruplar = {}
            adaylar = sorted((c for c in secilen.values() if islem in c[0]["senaryo"]),
                             key=lambda c: (-c[0].get("oncelik", 0), -c[1], c[0]["kod"]))
            for r, _ in adaylar:
                veriler = [self.vergi_kaydi(r, k) for k in self.referans_kayitlari(r, kod)]
                veriler = [v for v in veriler if v is not None]
                if veriler:
                    gruplar.setdefault(r["tur"], []).extend(veriler)
                    self.kullanilan.add(r["kod"])
            if gruplar:
                sonuc[islem] = {
                    tur: self.ornek_atama(tur, islem, secenekler)
                    for tur, secenekler in gruplar.items()
                }
        return sonuc


def randiman_bilgisi(kod, girdi, cikti, oranlar, kural_by_kod):
    roller = defaultdict(set)
    for r in girdi.bul(kod):
        roller[r["kod"]].add("girdi")
    for r in cikti.bul(kod):
        roller[r["kod"]].add("cikti")
    if not roller:
        return None
    surecler = []
    for kural_kodu in sorted(roller):
        r = kural_by_kod[kural_kodu]
        grup = oranlar[r["randiman_kodu"]]
        # Örnek ana ürün verimi, gerçek üretim firesi değildir.
        ornek_oran = grup.get("ornek_randiman_orani")
        if ornek_oran is None:
            ornek_oran = (grup.get("ornek_oranlar") or {}).get("randiman_orani")
        aday = {"surec_kodu": r["randiman_kodu"],
                "rol": "/".join(sorted(roller[kural_kodu])),
                "durum": "kosullu_ornek", "kural": kural_kodu}
        if ornek_oran is not None:
            aday["randiman_orani"] = ornek_oran
        if grup.get("fire_orani") is not None and grup.get("fire_dogrulandi") is True:
            aday["fire_orani"] = grup["fire_orani"]
        surecler.append(aday)
    return surecler


def belge_bilgisi(kod, index, belge_kodlari):
    sonuc = {k: {} for k in ISLEMLER}
    for r in index.bul(kod):
        # Yalnızca resmî kaynağa bağlanmış, kapsamı belirtilmiş kurallar
        # konsolide kartlara taşınır; eski örnek kurallar taşınmaz.
        if r.get("durum") not in ("kosullu", "zorunlu") or not r.get("kaynak_ref"):
            continue
        for islem in r.get("islem_tipleri", ()):
            if islem not in sonuc:
                continue
            for belge in r.get("belge_kodlari", r.get("aday_belge_kodlari", ())):
                b = belge_kodlari.get(belge)
                if not b:
                    continue
                bilgi = {"kod": belge,
                    "ad_tr": kayit_adi(b, "tr"), "ad_en": kayit_adi(b, "en"),
                    "durum": r["durum"]}
                if r.get("kapsam"):
                    bilgi["kapsam"] = r["kapsam"]
                if r.get("kosul_etiketi"):
                    bilgi["kosul"] = r["kosul_etiketi"]
                if r.get("istisna_etiketi"):
                    bilgi["istisna"] = r["istisna_etiketi"]
                sonuc[islem].setdefault(belge, bilgi)
    return {k: list(d.values()) for k, d in sonuc.items()}


def siniflama_bilgisi(kod, index, cpc_kodlari, nace_kodlari, randiman, kural_by_kod):
    cpc, nace = {}, {}
    eslesen = index.bul(kod)
    if eslesen:
        en_uzun = max((len(str(p)) for r in eslesen for p in r.get("gtip_prefixler", []) if kod.startswith(str(p))), default=0)
        for r in eslesen:
            if not any(kod.startswith(str(p)) and len(str(p)) == en_uzun for p in r.get("gtip_prefixler", [])):
                continue
            for k in r.get("cpc_kodlari", []):
                if k in cpc_kodlari:
                    x = cpc_kodlari[k]
                    cpc.setdefault(k, {"kod": k, "ad_tr": kayit_adi(x, "tr"), "ad_en": kayit_adi(x, "en")})
            for k in r.get("nace_kodlari", []):
                if k in nace_kodlari:
                    x = nace_kodlari[k]
                    nace.setdefault(k, {"kod": k, "ad_tr": kayit_adi(x, "tr"), "ad_en": kayit_adi(x, "en")})
    for surec in randiman or []:
        if "cikti" not in surec["rol"]:
            continue
        r = kural_by_kod[surec["kural"]]
        for k in r.get("nace_referans_kodlari", []):
            if k in nace_kodlari and k not in nace:
                x = nace_kodlari[k]
                nace[k] = {"kod": k, "ad_tr": kayit_adi(x, "tr"), "ad_en": kayit_adi(x, "en")}
    return list(cpc.values()), list(nace.values())


def kaynak_listesi(ham_d, kural_d):
    sonuc = []
    gorulen = set()
    for d in list(ham_d.values()) + list(kural_d.values()):
        bilgiler = d["meta"].get("kaynaklar", [])
        kaynaklar = bilgiler.get("referanslar", []) if isinstance(bilgiler, dict) else bilgiler
        for kaynak in kaynaklar:
            if not isinstance(kaynak, dict):
                continue
            belirtec = kaynak.get("kod") or kaynak.get("url") or json.dumps(kaynak, sort_keys=True, ensure_ascii=False)
            if belirtec not in gorulen:
                gorulen.add(belirtec)
                sonuc.append(kaynak)
    return sonuc


def mevzuat_listesi(ham_d, kural_d):
    sonuc = []
    gorulen = set()
    for d in list(ham_d.values()) + list(kural_d.values()):
        bilgiler = d["meta"].get("kaynaklar", {})
        mevzuat = d["meta"].get("mevzuat_ref") or (bilgiler.get("mevzuat", []) if isinstance(bilgiler, dict) else [])
        for kaynak in mevzuat:
            imza = json.dumps(kaynak, sort_keys=True, ensure_ascii=False)
            if imza not in gorulen:
                gorulen.add(imza)
                sonuc.append(kaynak)
    return sonuc


def schema():
    kimlik = {"kod": {"type": "string"}, "ust_kod": {"type": "string"}, "yaprak": {"type": "boolean"}, "seviye": {"type": "integer"}, "ad_tr": {"type": "string"}, "ad_en": {"type": "string"}, "olcu_birimi": {"type": "string"}}
    oran = {"type": ["number", "null"]}
    vergi_turu = {"type": "object", "required": ["ref"],
                  "properties": {"ref": {"type": "string"},
                                 "durum": {"type": "string"},
                                 "uygulama": {"type": "string"},
                                 "oran": {"type": "number"},
                                 "tutar": {"type": "number"},
                                 "birim": {"type": "string"},
                                 "para_birimi": {"type": "string"},
                                 "kesir": {"type": "string"},
                                 "istisna": {"type": "boolean"},
                                 "mense_grubu": {"type": "string"},
                                 "mense_varsayimi": {"type": "string"},
                                 "igv_mense_grubu": {"type": "string"},
                                 "gv": {"type": "number"},
                                 "igv": {"type": "number"},
                                 "igv_ref": {"type": "string"},
                                 "kapsam": {"type": "string"},
                                 "alici_gruplari": {"type": "array", "items": {"type": "string"}}}}
    vergi = {"type": "object", "additionalProperties": {"type": "object",
                                              "additionalProperties": vergi_turu}}
    alanlar = {
        "urun_karti": {"type": "boolean"},
        "cpc": {"type": "array", "items": {"type": "object", "required": ["kod", "ad_tr", "ad_en"]}},
        "nace": {"type": "array", "items": {"type": "object", "required": ["kod", "ad_tr", "ad_en"]}},
        "vergi": vergi,
        "randiman": {"type": "array", "items": {"type": "object", "properties": {"randiman_orani": oran, "fire_orani": oran}}},
        "belgeler": {"type": "object", "required": list(ISLEMLER), "properties": {
            k: {"type": "array", "items": {"type": "object", "required": ["kod", "ad_tr", "ad_en", "durum"],
                 "properties": {"kod": {"type": "string"}, "ad_tr": {"type": "string"},
                                "ad_en": {"type": "string"}, "durum": {"enum": ["kosullu", "zorunlu"]},
                                "kapsam": {"enum": ["urun", "isletme", "sevk"]},
                                "kosul": {"type": "object", "required": ["tr", "en"],
                                          "properties": {"tr": {"type": "string"}, "en": {"type": "string"}}},
                                "istisna": {"type": "object", "required": ["tr", "en"],
                                            "properties": {"tr": {"type": "string"}, "en": {"type": "string"}}}}}}
            for k in ISLEMLER}},
    }
    kart = {"type": "object", "required": ["kod", "seviye", "yaprak", "ad_tr", "ad_en"], "properties": {**kimlik, **alanlar}}
    gtip_kod_listesi = {"type": "array", "minItems": 1, "uniqueItems": True,
                        "items": {"type": "string", "pattern": "^[0-9]{12}$"}}
    kod_adi = {"type": "object", "required": ["kod", "ad_tr", "ad_en"],
               "properties": {"kod": {"type": "string"}, "ad_tr": {"type": "string"},
                              "ad_en": {"type": "string"}}}
    vergi_ozet_turu = {"type": "object", "required": ["ref", "gtip_kodlari"],
                       "properties": {**vergi_turu["properties"], "gtip_kodlari": gtip_kod_listesi}}
    vergi_ozeti = {"type": "object", "additionalProperties": {"type": "object",
                   "additionalProperties": {"type": "array", "minItems": 1, "items": vergi_ozet_turu}}}
    belge_ozeti = {"type": "object", "properties": {
        k: {"type": "array", "minItems": 1, "items": {"type": "object",
            "required": ["kod", "ad_tr", "ad_en", "durum", "gtip_kodlari"],
            "properties": {"kod": {"type": "string"}, "ad_tr": {"type": "string"},
                           "ad_en": {"type": "string"}, "durum": {"type": "string"},
                           "kapsam": {"type": "string"}, "kosul": {"type": "object"},
                           "istisna": {"type": "object"}, "gtip_kodlari": gtip_kod_listesi}}}
        for k in ISLEMLER}}
    konsolide_sinif = {"type": "object", "required": ["kod", "seviye", "yaprak", "ad_tr", "ad_en"],
        "properties": {**kimlik, "gtip": {"type": "array", "minItems": 1, "items": kod_adi},
                       "cpc": {"type": "array", "minItems": 1, "items": kod_adi},
                       "nace": {"type": "array", "minItems": 1, "items": kod_adi},
                       "isco": {"type": "array", "minItems": 1, "items": kod_adi},
                       "tesvik_adaylari": {"type": "array", "minItems": 1, "items": {
                           "type": "object", "required": ["kod", "ad_tr", "ad_en", "durum"],
                           "properties": {"kod": {"type": "string"}, "ad_tr": {"type": "string"},
                                          "ad_en": {"type": "string"},
                                          "durum": {"const": "kosullu"},
                                          "puan": {"type": "number"}}}},
                       "vergi": vergi_ozeti, "belgeler": belge_ozeti,
                       "randiman": {"type": "array", "items": {"type": "object",
                                    "required": ["gtip_kodu", "surecler"],
                                    "properties": {"gtip_kodu": {"type": "string"},
                                                   "surecler": {"type": "array"}}}}}}
    faaliyet_belge_ozet = {"type": "object",
        "required": ["kod", "ad_tr", "ad_en", "tur", "durum", "kaynak_ref", "kosul"],
        "properties": {"kod": {"type": "string"}, "ad_tr": {"type": "string"},
                       "ad_en": {"type": "string"}, "tur": {"type": "string"},
                       "durum": {"const": "kosullu"}, "kaynak_ref": {"type": "string"},
                       "kosul": {"type": "object", "required": ["tr", "en"],
                                  "properties": {"tr": {"type": "string"},
                                                 "en": {"type": "string"}}}}}
    nace_sinif = {**konsolide_sinif,
        "properties": {**{k: v for k, v in konsolide_sinif["properties"].items()
                          if k not in ("vergi", "randiman", "belgeler")},
                       "belgeler": {"type": "array", "minItems": 1,
                                    "items": faaliyet_belge_ozet}}}
    sgk_ozet = {"type": "object", "required": ["kod", "ad_tr", "ad_en"],
                "properties": {"kod": {"type": "string", "pattern": r"^\d{4}\.\d{2}$"},
                               "ad_tr": {"type": "string"}, "ad_en": {"type": "string"}}}
    isco_kart = {"type": "object", "required": ["kod", "seviye", "yaprak", "ad_tr", "ad_en"],
                 "properties": {**kimlik, "sgk": {"type": "array", "items": sgk_ozet},
                                "sgk_adaylari": {"type": "array", "items": sgk_ozet},
                                "nace": {"type": "array", "minItems": 1, "items": kod_adi},
                                "mesleki_belgeler": {"type": "array", "minItems": 1,
                                    "items": {"type": "object",
                                        "required": ["kod", "ad_tr", "ad_en", "tur", "durum", "kaynak_ref"],
                                        "properties": {"kod": {"type": "string"},
                                                       "ad_tr": {"type": "string"},
                                                       "ad_en": {"type": "string"},
                                                       "tur": {"type": "string"},
                                                       "durum": {"enum": ["zorunlu", "kosullu"]},
                                                       "kaynak_ref": {"type": "string"},
                                                       "kosul": {"type": "object", "required": ["tr", "en"],
                                                           "properties": {"tr": {"type": "string"},
                                                                          "en": {"type": "string"}}}}}}}}
    meta = {"type": "object", "required": ["servis", "katman", "versiyon", "guncelleme", "yapi"]}
    return {"schema_surumu": SURUM, "schemas": {
        "gtip-konsolide": {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "GTİP Konsolide Ürün Kartları", "type": "object", "required": ["meta", "kayitlar"], "properties": {"meta": meta, "kayitlar": {"type": "array", "items": kart}}},
        "cpc-konsolide": {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "CPC Konsolide Ürün ve Hizmet Kartları", "type": "object", "required": ["meta", "kayitlar"], "properties": {"meta": meta, "kayitlar": {"type": "array", "items": konsolide_sinif}}},
        "nace-konsolide": {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "NACE Konsolide Faaliyet Kartları", "type": "object", "required": ["meta", "kayitlar"], "properties": {"meta": meta, "kayitlar": {"type": "array", "items": nace_sinif}}},
        "isco-konsolide": {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "ISCO Konsolide Meslek Kartları", "type": "object", "required": ["meta", "kayitlar"], "properties": {"meta": meta, "kayitlar": {"type": "array", "items": isco_kart}}},
    }}


def katalog_olustur(kok, tarih):
    """Üretim bittikten sonra v1 kökündeki gerçek JSON servislerini keşfeder."""
    servisler = {}
    for yol in sorted(kok.glob("*.json")):
        # Kataloğun kendisi ve artık üretilmeyen tarihsel dosyalar servis değildir.
        if yol.name == "katalog.json" or yol.stem in ESKI_SERVISLER:
            continue
        d = oku(yol)
        m = d["meta"]
        # Konsolide meta.checksum, doğrudan kayıt dizisinin SHA-256 özetidir.
        if m.get("katman") == "konsolide" and isinstance(d.get("kayitlar"), list):
            checksum = sha_nesne(d["kayitlar"])
            if m.get("checksum") and m["checksum"] != checksum:
                raise ValueError(f"{yol.name}: konsolide checksum uyuşmuyor")
        else:
            checksum = sha_nesne(icerik(d))
        r = katalog_kaydi(d, yol.name, checksum)
        kod = r["kod"]
        if kod in servisler:
            onceki = servisler[kod]
            for katman, bilgi in r["katmanlar"].items():
                if katman in onceki["katmanlar"]:
                    raise ValueError(f"Katalogda mükerrer servis ve katman: {kod}/{katman}")
                onceki["katmanlar"][katman] = bilgi
        else:
            servisler[kod] = r
    return {"schema_surumu": SURUM, "dosya_surumu": SURUM, "surum": SURUM, "guncelleme": tarih, "servisler": sorted(servisler.values(), key=lambda s: s["kod"])}


def katalog_kaydi(d, dosya, checksum):
    m = d["meta"]
    servis = m.get("servis", {})
    kod = servis if isinstance(servis, str) else servis.get("kod")
    kod = kod or m.get("servis_kodu") or Path(dosya).stem
    ad = (servis.get("ad") if isinstance(servis, dict) else None)
    ad = ad or m.get("uluslararasi", {}).get("baslik") or m.get("servis_adi")
    if isinstance(ad, str):
        ad = {"tr": ad, "en": ad}
    if not isinstance(ad, dict):
        ad = {"tr": kod, "en": kod}
    ad = {"tr": ad.get("tr") or kod, "en": ad.get("en") or ad.get("tr") or kod}
    yapi = m.get("yapi") or {}
    sistem = yapi.get("sistem") or yapi.get("kod_sistemi") or kod
    katman = m.get("katman") or ("kurallar" if dosya.endswith("-kurallar.json")
                                  else "konsolide" if dosya.endswith("-konsolide.json")
                                  else "ham")
    if katman == "kural":
        katman = "kurallar"  # Katalogda tek kural grubu; kaynak meta değiştirilmez.
    tip = yapi.get("tip") or ("kural-seti" if "kurallar" in d else "liste")
    surumler = m.get("versiyon")
    surum = (surumler.get("dosya") if isinstance(surumler, dict) else None) or m.get("dosya_surumu") or SURUM
    return {"kod": kod, "ad": ad, "tip": tip, "kod_sistemi": sistem,
            "katmanlar": {katman: {"son": surum, "url": API_YOLU + "/" + dosya,
                                  "surumler_url": None, "checksum": checksum}}}


def derle(kok, tarih):
    ham = {k: oku(kok / ad) for k, ad in HAM.items()}
    for tur in ("gtip", "cpc", "nace"):
        eksikler = [str(r.get("kod", "?")) for r in ham[tur].get("kayitlar", []) if not kayit_adi(r, "tr") or not kayit_adi(r, "en")]
        if eksikler:
            raise ValueError(f"{HAM[tur]}: ad_tr/ad_en eksik olan {len(eksikler)} kayıt var. İlk kodlar: {', '.join(eksikler[:5])}")
    kural_isimleri = dict(KURALLAR)
    gorunum_yolu = kok / GORUNUM_DOSYASI
    if gorunum_yolu.is_file():
        kural_isimleri["gorunum"] = GORUNUM_DOSYASI
    else:
        print(f"[UYARI] {GORUNUM_DOSYASI} yok; özel istatistik kayıtları ürün kartı görünümünden ayrılmayacak.", flush=True)
    kurallar = {k: oku(kok / ad) for k, ad in kural_isimleri.items()}
    belge_kurallari = belge_kural_bolumleri(kurallar["belgeler"])
    nace_tesvikler, tesvik_sayac = nace_tesvik_adaylari(
        ham["nace"], ham["tesvik"], kurallar["tesvik"])
    nace_belgeler, faaliyet_belge_sayac = nace_faaliyet_belgeleri(
        ham["nace"], ham["faaliyet_belgeleri"], belge_kurallari["faaliyet_kurallari"])
    isco_kayitlar, isco_sayac = isco_sgk_kartlari(ham["isco"], ham["sgk_meslek"])
    isco_mesleki_belgeler, mesleki_belge_sayac = isco_mesleki_belge_baglantilari(
        ham["isco"], ham["mesleki_belgeler"], belge_kurallari["meslek_kurallari"])
    isco_to_nace, nace_to_isco, isco_nace_sayac = isco_nace_baglantilari(
        ham["isco"], ham["nace"], kurallar["siniflama"])
    for item in isco_kayitlar:
        if item["kod"] in isco_to_nace:
            item["nace"] = isco_to_nace[item["kod"]]
        if item["kod"] in isco_mesleki_belgeler:
            item["mesleki_belgeler"] = isco_mesleki_belgeler[item["kod"]]
    kayitlar = ham["gtip"].get("kayitlar", [])
    if not kayitlar or len({str(x["kod"]) for x in kayitlar}) != len(kayitlar):
        raise ValueError("GTİP listesi boş veya mükerrer kod içeriyor")
    birimi_eksik_alan = [str(r["kod"]) for r in kayitlar if r.get("yaprak") and not r.get("olcu_birimi")]
    if birimi_eksik_alan:
        print(f"[UYARI] {len(birimi_eksik_alan)} yaprak GTİP kaydında ölçü birimi bulunamadı; boş bırakıldı.", flush=True)
    gorunum_haric = gorunum_haric_kodlari(kurallar.get("gorunum"), kayitlar)
    sozluk = {k: {r["kod"]: r for r in ham[k]["kayitlar"]} for k in ("cpc", "nace", "randiman", "belgeler")}
    vergi_ham = {"kdv": ham["kdv"], "otv": ham["otv"], "tevkifat": ham["tevkifat"],
                 "gumruk-vergisi": ham["gumruk"]}
    urun_vergi_kurallari = [r for r in kurallar["vergi"]["kurallar"] if r["tur"] != "damga-vergisi"]
    vergi_index = VergiIndex(urun_vergi_kurallari, vergi_ham, tarih)
    idx = {
        "belgeler": PrefixIndex(belge_kurallari["urun_kurallari"], "gtip_prefixler"),
        "girdi": PrefixIndex(kurallar["randiman"]["kurallar"], "girdi_gtip_prefixler"),
        "cikti": PrefixIndex(kurallar["randiman"]["kurallar"], "cikti_gtip_prefixler"),
        "siniflama": PrefixIndex(kurallar["siniflama"]["kurallar"], "gtip_prefixler"),
    }
    ran_kurallar = {r["kod"]: r for r in kurallar["randiman"]["kurallar"]}
    if len(ran_kurallar) != len(kurallar["randiman"]["kurallar"]):
        raise ValueError("randiman-kurallar.json: mükerrer kural kodu")
    for r in ran_kurallar.values():
        ref = r.get("randiman_kodu")
        if ref not in sozluk["randiman"]:
            raise ValueError(f"{r['kod']}: randiman.json içinde bulunmayan referans: {ref}")
        if not r.get("girdi_gtip_prefixler") or not r.get("cikti_gtip_prefixler"):
            raise ValueError(f"{r['kod']}: girdi ve çıktı GTİP önekleri zorunludur")
        oran = sozluk["randiman"][ref].get("ornek_randiman_orani")
        if oran is not None and (not isinstance(oran, (int, float)) or isinstance(oran, bool) or not 0 < oran <= 1):
            raise ValueError(f"{ref}: örnek randıman oranı 0 ile 1 arasında olmalı")
    dosyalar = []
    for katman, kaynak, isimler in (("ham", ham, HAM), ("kurallar", kurallar, kural_isimleri)):
        for k, ad in isimler.items():
            d = kaynak[k]
            yol = kok / ad
            checksum = sha_nesne(icerik(d))
            servis = d["meta"]["servis"]
            dosyalar.append({"dosya": ad, "servis_kodu": servis if isinstance(servis, str) else servis["kod"],
                            "surum": d["meta"].get("versiyon", {}).get("dosya", d["meta"].get("surum", SURUM)),
                            "dosya_sha256": sha_dosya(yol), "icerik_sha256": checksum})
    with tempfile.TemporaryDirectory(prefix=".pdaas-derle-", dir=kok) as tmp:
        tmp = Path(tmp)
        y = KayitYazici(tmp / "kayitlar.jsonl")
        sayac = Counter()
        cpc_to_gtip = defaultdict(set)
        nace_to_gtip = defaultdict(set)
        gtip_kartlari = {}
        for no, r in enumerate(kayitlar, 1):
            kart = kimlik_karti(r)
            kart["kod"] = str(r["kod"])
            if r.get("yaprak"):
                kod = kart["kod"]
                kart["urun_karti"] = kod not in gorunum_haric
                sayac["yaprak"] += 1
                if not kart["urun_karti"]:
                    kart.update({"cpc": [], "nace": [], "vergi": {}, "randiman": [], "belgeler": {k: [] for k in ISLEMLER}})
                    sayac["ozel_istatistik"] += 1
                else:
                    ran = randiman_bilgisi(kod, idx["girdi"], idx["cikti"], sozluk["randiman"], ran_kurallar)
                    bel = belge_bilgisi(kod, idx["belgeler"], sozluk["belgeler"])
                    cpc, nace = siniflama_bilgisi(kod, idx["siniflama"], sozluk["cpc"], sozluk["nace"], ran, ran_kurallar)
                    vergi = vergi_index.bul(kod, [x["kod"] for x in cpc])
                    for es in cpc:
                        cpc_to_gtip[es["kod"]].add(kod)
                    for es in nace:
                        nace_to_gtip[es["kod"]].add(kod)
                    ran_kart = [{k: v for k, v in surec.items() if k != "kural" and v is not None}
                                for surec in (ran or [])]
                    kart.update({"cpc": cpc, "nace": nace, "vergi": vergi,
                                 "randiman": ran_kart, "belgeler": bel})
                    if cpc or nace:
                        gtip_kartlari[kod] = kart
                    sayac["urun_karti"] += 1
                    for alan, deger in (("cpc", cpc), ("nace", nace), ("vergi", vergi), ("randiman", ran)):
                        if deger:
                            sayac[alan + "_eslesen"] += 1
                    if any(bel.values()):
                        sayac["belge_eslesen"] += 1
            y.ekle(kart)
            if no % 10000 == 0:
                print(f"{no:,}/{len(kayitlar):,} GTİP işlendi", flush=True)
        checksum = y.bitir()
        kaynak_referanslari = kaynak_listesi(ham, kurallar)
        mevzuat = mevzuat_listesi(ham, kurallar)
        meta = {
            "versiyon": {"schema": SURUM, "dosya": SURUM, "veri": SURUM},
            "servis": "gtip-konsolide", "katman": "konsolide", "durum": "yayinda",
            "guncelleme": tarih,
            "yapi": {"tip": "agac", "sistem": "gtip", "kapsam": "urun",
                     "kayit_sayisi": len(kayitlar), "yaprak_sayisi": sayac["yaprak"],
                     "donem_sonu": "2026-12-31"},
            "uluslararasi": {"dil": ["tr", "en"], "baslik": SERVIS_ADI},
            "kaynaklar": {"dosyalar": list(VERI_DOSYALARI) +
                         ([GORUNUM_DOSYASI] if gorunum_yolu.is_file() else [])},
            "checksum": checksum,
            "tablo_haritasi": {"pk": "kod", "ust_id": "ust_kod",
                               "kolonlar": ["kod", "ust_kod", "seviye", "yaprak",
                                            "ad_tr", "ad_en", "olcu_birimi",
                                            "cpc", "nace", "vergi", "randiman", "belgeler"]},
        }
        if gorunum_yolu.is_file():
            meta["gorunum_kurallari_ref"] = GORUNUM_DOSYASI
        tam = tmp / "gtip-konsolide.json"
        with tam.open("w", encoding="utf-8") as f:
            f.write('{"meta":')
            json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))
            f.write(',"kayitlar":[')
            with y.yol.open(encoding="utf-8") as satirlar:
                for no, satir in enumerate(satirlar):
                    f.write(("," if no else "") + "\n" + satir.rstrip("\n"))
            f.write("\n]}\n")
        cpc_kayitlar = []
        for r in ham["cpc"]["kayitlar"]:
            item = kimlik_karti(r)
            item["kod"] = str(r["kod"])
            if cpc_to_gtip.get(item["kod"]):
                item.update(iliskisel_kart_ozeti(cpc_to_gtip[item["kod"]], gtip_kartlari, "nace"))
            cpc_kayitlar.append(item)
        cpc_checksum = sha_nesne(cpc_kayitlar)
        cpc_meta = {
            **meta, "servis": "cpc-konsolide",
            "uluslararasi": {"dil": ["tr", "en"], "baslik": CPC_SERVIS_ADI},
            "yapi": {"tip": "agac", "sistem": "cpc", "kapsam": ["urun", "hizmet"],
                     "kayit_sayisi": len(cpc_kayitlar),
                     "iliski_sayisi": sum(len(v) for v in cpc_to_gtip.values()),
                     "eslesen_kayit_sayisi": sum(bool(v) for v in cpc_to_gtip.values()),
                     "sistem_surumu": ham["cpc"]["meta"]["yapi"].get("sistem_surumu", "3.0")},
            "checksum": cpc_checksum,
            "tablo_haritasi": {"pk": "kod", "ust_id": "ust_kod",
                               "kolonlar": ["kod", "ust_kod", "seviye", "yaprak", "ad_tr", "ad_en",
                                            "gtip", "nace", "vergi", "belgeler", "randiman"]},
        }
        cpc_meta.pop("gorunum_kurallari_ref", None)
        cpc_gecici = tmp / "cpc-konsolide.json"
        yaz(cpc_gecici, {"meta": cpc_meta, "kayitlar": cpc_kayitlar})
        nace_kayitlar = []
        for r in ham["nace"]["kayitlar"]:
            item = kimlik_karti(r)
            item["kod"] = str(r["kod"])
            if nace_to_gtip.get(item["kod"]):
                item.update(iliskisel_kart_ozeti(nace_to_gtip[item["kod"]], gtip_kartlari,
                                                   "cpc", uygulama_bilgileri=False))
            if nace_to_isco.get(item["kod"]):
                item["isco"] = nace_to_isco[item["kod"]]
            if nace_tesvikler.get(item["kod"]):
                item["tesvik_adaylari"] = nace_tesvikler[item["kod"]]
            if nace_belgeler.get(item["kod"]):
                item["belgeler"] = nace_belgeler[item["kod"]]
            nace_kayitlar.append(item)
        nace_checksum = sha_nesne(nace_kayitlar)
        nace_ham_yapi = ham["nace"]["meta"]["yapi"]
        nace_meta = {
            **meta, "servis": "nace-konsolide",
            "uluslararasi": {"dil": ["tr", "en"], "baslik": NACE_SERVIS_ADI},
            "yapi": {"tip": "agac", "sistem": "nace", "kapsam": "faaliyet",
                     "kayit_sayisi": len(nace_kayitlar),
                     "iliski_sayisi": sum(len(v) for v in nace_to_gtip.values()),
                     "eslesen_kayit_sayisi": sum(bool(v) for v in nace_to_gtip.values()),
                     "isco_iliski_sayisi": isco_nace_sayac["iliski"],
                     "isco_ile_eslesen_kayit_sayisi": isco_nace_sayac["nace_faaliyeti"],
                     "isco_iliskisi": "olasi_faaliyet",
                     "tesvik_aday_iliski_sayisi": tesvik_sayac["aday_iliski_sayisi"],
                     "tesvik_adayi_bulunan_kayit_sayisi": tesvik_sayac["eslesen_nace_kayit_sayisi"],
                     "tesvik_iliskisi": "kosullu_aday",
                     "faaliyet_belge_iliski_sayisi": faaliyet_belge_sayac["iliski"],
                     "faaliyet_belgeli_kayit_sayisi": faaliyet_belge_sayac["eslesen_kayit"],
                     "sistem_surumu": nace_ham_yapi.get("sistem_surumu", "Rev.2.1"),
                     "ulusal_surumu": nace_ham_yapi.get("ulusal_surumu", "2026"),
                     "eslesme_seviyesi": 4},
            "checksum": nace_checksum,
            "kaynaklar": {"dosyalar": [HAM["nace"], HAM["gtip"], HAM["cpc"],
                                       HAM["isco"], KURALLAR["siniflama"],
                                       HAM["randiman"], KURALLAR["randiman"],
                                       HAM["tesvik"], KURALLAR["tesvik"],
                                       HAM["faaliyet_belgeleri"], KURALLAR["belgeler"]],
                          "referanslar": ham["faaliyet_belgeleri"]["meta"]["kaynaklar"]["referanslar"]},
            "tablo_haritasi": {"pk": "kod", "ust_id": "ust_kod",
                               "kolonlar": ["kod", "ust_kod", "seviye", "yaprak", "ad_tr", "ad_en",
                                            "gtip", "cpc", "isco", "belgeler", "tesvik_adaylari"]},
        }
        nace_meta.pop("gorunum_kurallari_ref", None)
        nace_gecici = tmp / "nace-konsolide.json"
        yaz(nace_gecici, {"meta": nace_meta, "kayitlar": nace_kayitlar})
        isco_checksum = sha_nesne(isco_kayitlar)
        isco_ham_yapi = ham["isco"]["meta"]["yapi"]
        isco_meta = {
            "versiyon": {"schema": SURUM, "dosya": SURUM, "veri": SURUM},
            "servis": "isco-konsolide", "katman": "konsolide", "durum": "yayinda",
            "guncelleme": tarih,
            "yapi": {"tip": "agac", "sistem": "isco", "kapsam": "meslek",
                     "kayit_sayisi": len(isco_kayitlar),
                     "sistem_surumu": isco_ham_yapi.get("sistem_surumu", isco_ham_yapi.get("kod_sistemi_surumu", "ISCO-08")),
                     "iliski_sayisi": isco_sayac["dogrulanan"],
                     "aday_iliski_sayisi": isco_sayac["aday"],
                     "eslesen_kayit_sayisi": isco_sayac["dogrulanan_isco_grubu"],
                     "adayli_kayit_sayisi": isco_sayac["adayli_isco_grubu"],
                     "nace_iliski_sayisi": isco_nace_sayac["iliski"],
                     "nace_ile_eslesen_kayit_sayisi": isco_nace_sayac["isco_grubu"],
                     "mesleki_belge_iliski_sayisi": mesleki_belge_sayac["iliski"],
                     "mesleki_belge_eslesen_kayit_sayisi": mesleki_belge_sayac["meslek"],
                     "nace_iliskisi": "olasi_faaliyet"},
            "uluslararasi": {"dil": ["tr", "en"], "baslik": ISCO_SERVIS_ADI},
            "kaynaklar": {"dosyalar": [HAM["isco"], HAM["sgk_meslek"], KURALLAR["siniflama"], HAM["nace"], HAM["mesleki_belgeler"], KURALLAR["belgeler"]],
                          "referanslar": ham["mesleki_belgeler"]["meta"]["kaynaklar"]["referanslar"]},
            "checksum": isco_checksum,
            "tablo_haritasi": {"pk": "kod", "ust_id": "ust_kod",
                               "kolonlar": ["kod", "ust_kod", "seviye", "yaprak",
                                            "ad_tr", "ad_en", "sgk", "sgk_adaylari", "nace", "mesleki_belgeler"]},
        }
        isco_gecici = tmp / "isco-konsolide.json"
        yaz(isco_gecici, {"meta": isco_meta, "kayitlar": isco_kayitlar})
        hedef = kok / "gtip-konsolide.json"
        cpc_hedef = kok / "cpc-konsolide.json"
        nace_hedef = kok / "nace-konsolide.json"
        isco_hedef = kok / "isco-konsolide.json"
        os.replace(tam, hedef)
        os.replace(cpc_gecici, cpc_hedef)
        os.replace(nace_gecici, nace_hedef)
        os.replace(isco_gecici, isco_hedef)
    schema_yol = kok / "meta/schema.json"
    mevcut_schema = varsa_oku(schema_yol)
    yeni_schema = schema()
    if mevcut_schema is not None:
        if not isinstance(mevcut_schema, dict) or not isinstance(mevcut_schema.get("schemas"), dict):
            raise ValueError(f"Mevcut şema biçimi tanınmadı, değiştirilmedi: {schema_yol}")
        mevcut_schemas = {k: v for k, v in mevcut_schema["schemas"].items()
                          if k not in ESKI_SERVISLER}
        yeni_schema["schemas"] = {**mevcut_schemas, **yeni_schema["schemas"]}
    yaz(schema_yol, yeni_schema)
    yaz(kok / "meta/kaynaklar.json", {"meta": {"versiyon": {"schema": SURUM, "dosya": SURUM, "veri": SURUM}}, "kaynaklar": kaynak_referanslari})
    yaz(kok / "meta/mevzuat.json", {"meta": {"versiyon": {"schema": SURUM, "dosya": SURUM, "veri": SURUM}}, "mevzuat_ref": mevzuat})
    katalog_yol = kok / "katalog.json"
    katalog = katalog_olustur(kok, tarih)
    yaz(katalog_yol, katalog)
    yaz(kok / "meta/derleme-raporu.json", {
        "surum": SURUM, "derleme_tarihi": tarih,
        "ciktilar": [
            {"dosya": "gtip-konsolide.json", "kayit_sayisi": len(kayitlar), "checksum": checksum, "dosya_sha256": sha_dosya(hedef)},
            {"dosya": "cpc-konsolide.json", "kayit_sayisi": len(cpc_kayitlar), "checksum": cpc_checksum, "dosya_sha256": sha_dosya(cpc_hedef)},
            {"dosya": "nace-konsolide.json", "kayit_sayisi": len(nace_kayitlar), "checksum": nace_checksum, "dosya_sha256": sha_dosya(nace_hedef)},
            {"dosya": "isco-konsolide.json", "kayit_sayisi": len(isco_kayitlar), "checksum": isco_checksum, "dosya_sha256": sha_dosya(isco_hedef)}],
        "yaprak_sayisi": sayac["yaprak"],
        "eslesme_sayaclari": dict(sayac),
        "isco_sgk_eslesme_sayaclari": dict(isco_sayac),
        "isco_nace_eslesme_sayaclari": dict(isco_nace_sayac),
        "nace_tesvik_eslesme_sayaclari": dict(tesvik_sayac),
        "isco_mesleki_belge_eslesme_sayaclari": dict(mesleki_belge_sayac),
        "nace_faaliyet_belgesi_eslesme_sayaclari": dict(faaliyet_belge_sayac),
        "kaynak_dosyalar": dosyalar})
    for ad in ("cpc-gtip", "nace-gtip", "nace-cpc"):
        eski_dosya = kok / (ad + ".json")
        if eski_dosya.is_file():
            eski = varsa_oku(eski_dosya)
            eski_meta = eski.get("meta", {}) if isinstance(eski, dict) else {}
            if (eski_meta.get("servis") == ad and isinstance(eski.get("kayitlar"), list)
                    and eski_meta.get("checksum") == sha_nesne(eski["kayitlar"])):
                eski_dosya.unlink()
                print(f"Eski konsolide dosya kaldırıldı: {eski_dosya.name}", flush=True)
            else:
                print(f"[UYARI] İçeriği değiştirilmiş olabilecek eski dosya korunuyor: {eski_dosya}", flush=True)
    for ad in ESKI_SERVISLER:
        eski_dosya = kok / (ad + ".json")
        if eski_dosya.exists():
            print(f"[UYARI] Önceki sürümden kalan dosya (artık üretilmiyor): {eski_dosya}", flush=True)
    print(f"Tamamlandı: {len(kayitlar):,} GTİP ({sayac['urun_karti']:,} ürün kartı); "
          f"{len(cpc_kayitlar):,} CPC; {len(nace_kayitlar):,} NACE; {len(isco_kayitlar):,} ISCO; "
          f"{faaliyet_belge_sayac['iliski']:,} NACE faaliyet belgesi bağlantısı; "
          f"{tesvik_sayac['aday_iliski_sayisi']:,} NACE teşvik adayı; 4 konsolide dosya", flush=True)


def main():
    ap = argparse.ArgumentParser(description="PDaaS GTİP, CPC, NACE ve ISCO konsolide kart derleyicisi")
    araclar = Path(__file__).resolve().parent
    kok = araclar.parent if araclar.name.lower() == "araclar" else araclar
    ap.add_argument("--kok", type=Path, default=kok)
    ap.add_argument("--tarih", default="2026-10-01")
    a = ap.parse_args()
    datetime.strptime(a.tarih, "%Y-%m-%d")
    kok = a.kok.resolve()
    derle(kok, a.tarih)


if __name__ == "__main__":
    main()
