# api/v1/araclar/kural_motoru.py

import hashlib
import json
import shutil
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Yollar ──────────────────────────────────────────────────────
V1        = Path(__file__).resolve().parents[1]
HAM       = V1 / "ham"
KURAL     = V1 / "kurallar"
BELGE     = V1 / "belgeler"
META      = V1 / "meta"
KONSOLIDE = V1 / "konsolide"

HEDEF_DOSYA      = KONSOLIDE / "gtip-konsolide.json"
CPC_HEDEF_DOSYA  = KONSOLIDE / "cpc-konsolide.json"
NACE_HEDEF_DOSYA = KONSOLIDE / "nace-konsolide.json"
ISCO_HEDEF_DOSYA = KONSOLIDE / "isco-konsolide.json"
KATALOG_DOSYA    = META / "katalog.json"

# ══════════════════════════════════════════════════════════════════
# SÜRÜM YÖNETİMİ
# ══════════════════════════════════════════════════════════════════
RELEASE = {
    "surum":       "1.0.0",
    "tarih":       "2026-11-01",
    "guncelleme":  "2026-11-01",
    "durum":       "demo",
    "force_all":   True,
}

current_kod = ""


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return "sha256:" + h.hexdigest()


def json_checksum(data: dict) -> str:
    """JSON özeti: meta.checksum alanı geçici olarak null kabul edilir."""
    clean = deepcopy(data)
    if isinstance(clean.get("meta"), dict):
        clean["meta"]["checksum"] = None
    raw = json.dumps(clean, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def json_yaz(path: Path, data: dict) -> None:
    """Meta checksum'unu hesaplayıp JSON'u tek biçimde yazar."""
    if isinstance(data.get("meta"), dict):
        data["meta"]["checksum"] = None
        data["meta"]["checksum"] = json_checksum(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def kayit_sayisini_bul(data: dict) -> int:
    for alan in ("kayitlar", "kurallar"):
        if isinstance(data.get(alan), list):
            return len(data[alan])
    kategoriler = data.get("kategoriler")
    if isinstance(kategoriler, dict):
        return sum(len(v.get("degerler", {})) for v in kategoriler.values()
                   if isinstance(v, dict) and isinstance(v.get("degerler"), dict))
    varliklar = data.get("varliklar")
    if isinstance(varliklar, dict):
        return sum(len(v) for v in varliklar.values() if isinstance(v, list))
    iliski_tablolari = data.get("iliski_tablolari")
    if isinstance(iliski_tablolari, dict):
        return sum(len(v) for v in iliski_tablolari.values() if isinstance(v, list))
    return 0


def meta_yenile(path: Path, data: dict) -> None:
    """Ortak meta sözleşmesini uygular; dosyaya özgü alanları detayda tutar."""
    meta = data.setdefault("meta", {})
    if not isinstance(meta, dict):
        meta = {}
        data["meta"] = meta

    kod = meta.get("kod") or path.stem.replace("-meta-ornek", "")
    schema = meta.get("schema")
    if not isinstance(schema, str) or "/" not in schema:
        schema = f"{kod}/v1"

    katman = meta.get("katman")
    if not katman:
        katman = {"ham": "ham", "kurallar": "kural", "belgeler": "ham",
                  "konsolide": "konsolide", "meta": "sozlesme"}.get(path.parent.name, "sozlesme")

    kurum = meta.get("sorumlu_kurum")
    if isinstance(kurum, dict):
        kurum = kurum.get("kod")
    if not kurum:
        kurum = "pdaas"

    detay = dict(meta.get("detay") or {})
    ortak = {
        "schema", "surum", "kod", "ad_tr", "ad_en", "tarih", "guncelleme",
        "durum", "katman", "kapsam", "islem_turleri", "yayinci",
        "sorumlu_kurum", "kaynaklar_ref", "mevzuat_ref", "sozluk_ref",
        "gecerlilik", "checksum", "kayit_sayisi", "detay",
    }
    for alan, deger in meta.items():
        if alan not in ortak:
            detay[alan] = deger

    if kod == "sozluk" and "changelog" in data:
        detay["changelog"] = data.pop("changelog")

    kaynaklar_ref = meta.get("kaynaklar_ref")
    mevzuat_ref = meta.get("mevzuat_ref")
    if kod not in {"sozluk", "kaynaklar", "mevzuat", "katalog", "manifest"}:
        kaynaklar_ref = kaynaklar_ref or "meta/kaynaklar.json"
        mevzuat_ref = mevzuat_ref or "meta/mevzuat.json"

    ad_tr = meta.get("ad_tr") or {"katalog": "Veri Kataloğu", "manifest": "Derleme Manifesti"}.get(kod, kod)
    ad_en = meta.get("ad_en") or {"katalog": "Data Catalog", "manifest": "Build Manifest"}.get(kod, kod)
    kapsam = meta.get("kapsam") or []
    islem_turleri = meta.get("islem_turleri") or []
    yayinci = meta.get("yayinci") or "pdaas"
    sozluk_ref = meta.get("sozluk_ref") or "meta/sozluk.json"
    gecerlilik = meta.get("gecerlilik") or {"baslangic": "2026-01-01", "bitis": None}

    meta.clear()
    meta.update({
        "schema": schema,
        "surum": RELEASE["surum"],
        "kod": kod,
        "ad_tr": ad_tr,
        "ad_en": ad_en,
        "tarih": RELEASE["tarih"],
        "guncelleme": RELEASE["guncelleme"],
        "durum": RELEASE["durum"],
        "katman": katman,
        "kapsam": kapsam,
        "islem_turleri": islem_turleri,
        "yayinci": yayinci,
        "sorumlu_kurum": kurum,
        "kaynaklar_ref": kaynaklar_ref,
        "mevzuat_ref": mevzuat_ref,
        "sozluk_ref": sozluk_ref,
        "gecerlilik": gecerlilik,
        "checksum": None,
        "kayit_sayisi": kayit_sayisini_bul(data),
        "detay": detay,
    })


# ══════════════════════════════════════════════════════════════════
# Sürüm güncelleme
# ══════════════════════════════════════════════════════════════════
def tum_surumleri_guncelle(force: bool = False, kuru: bool = False,
                           include_consolidated: bool = False) -> dict:
    hedefler = []
    klasorler = [HAM, KURAL, BELGE]
    if include_consolidated:
        klasorler.append(KONSOLIDE)
    for klasor in klasorler:
        if klasor.exists():
            hedefler.extend(sorted(klasor.glob("*.json")))

    if META.exists():
        hedefler.extend(p for p in sorted(META.glob("*.json"))
                        if p.name not in {"katalog.json", "manifest.json"})

    guncellenen = []
    atlanan = []
    hata = []

    for p in hedefler:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            hata.append((p.name, str(e)))
            continue

        if "meta" not in d:
            continue

        mevcut_surum = d.get("meta", {}).get("surum") if isinstance(d.get("meta"), dict) else None
        if not force and mevcut_surum and mevcut_surum != RELEASE["surum"]:
            atlanan.append((p.name, mevcut_surum))
            continue
        meta_yenile(p, d)
        if not kuru:
            json_yaz(p, d)
        guncellenen.append(p.relative_to(V1).as_posix())

    return {"guncellenen": guncellenen, "atlanan": atlanan, "hata": hata}


# ══════════════════════════════════════════════════════════════════
# KuralMotoru
# ══════════════════════════════════════════════════════════════════
class KuralMotoru:
    def __init__(self, kok: Optional[Path] = None):
        self.kok = Path(kok) if kok else V1
        self._yukle()

    def _yukle(self):
        ham   = self.kok / "ham"
        kural = self.kok / "kurallar"
        belge = self.kok / "belgeler"

        gtip_d = self._json(ham / "gtip-kodlari.json")
        self.gtip_idx = {r["kod"]: r for r in gtip_d.get("kayitlar", [])}

        cpc_d = self._json(ham / "cpc-kodlari.json")
        self.cpc_idx = {r["kod"]: r for r in cpc_d.get("kayitlar", [])}

        nace_d = self._json(ham / "nace-kodlari.json")
        self.nace_idx = {r["kod"]: r for r in nace_d.get("kayitlar", [])}

        isco_d = self._json(ham / "isco-kodlari.json")
        self.isco_idx = {r["kod"]: r for r in isco_d.get("kayitlar", [])}

        self.kdv_idx      = self._idx(ham / "kdv.json")
        self.otv_idx      = self._idx(ham / "otv.json")
        self.tevkifat_idx = self._idx(ham / "kdv-tevkifat.json")
        self.igv_idx      = self._idx(ham / "ilave-gumruk-vergisi.json")

        g = self._json(ham / "gumruk-vergisi.json")
        self.gumruk_sema = g.get("sema", {})
        self.gumruk_by_kod = {}
        for r in g.get("kayitlar", []):
            if r.get("ozel_durum") == "gtip_disi":
                continue
            self.gumruk_by_kod.setdefault(r["kod"], []).append(r)

        vk = self._json(kural / "vergi-kurallari.json")
        self.vergi_kurallari = [k for k in vk.get("kurallar", []) if k.get("aktif", True)]
        self.vergi_meta      = (vk.get("meta", {}).get("detay")
                                or vk.get("meta", {}))

        bk = self._json(kural / "belge-kurallari.json")
        self.belge_kurallari = [k for k in bk.get("kurallar", []) if k.get("aktif", True)]

        faaliyet_bk = self._json(kural / "nace-faaliyet-belge-kurallari.json")
        self.faaliyet_belge_kurallari = [
            k for k in faaliyet_bk.get("kurallar", []) if k.get("aktif", True)
        ]

        meslek_bk = self._json(kural / "isco-mesleki-belge-kurallari.json")
        self.meslek_belge_kurallari = [
            k for k in meslek_bk.get("kurallar", []) if k.get("aktif", True)
        ]

        self.belge_master = {}
        if belge.exists():
            for p in belge.glob("*.json"):
                if "kural" in p.name:
                    continue
                try:
                    bd = self._json(p)
                except Exception:
                    continue
                for r in bd.get("kayitlar", []):
                    if r.get("kod"):
                        self.belge_master[r["kod"]] = r

        iliski_d = self._json(kural / "kod-iliskileri.json")
        tablolar = iliski_d.get("iliski_tablolari", {})
        self.gtip_cpc_idx = {}
        self.gtip_nace_idx = {}
        self.nace_isco_idx = {}

        # İlişkileri tek kez indeksle; ad ve ref alanları kataloglardan gelir.
        self.cpc_to_gtip  = {}
        self.nace_to_gtip = {}
        self.nace_to_isco = {}
        self.nace_to_cpc  = {}
        self.isco_to_nace = {}

        for e in tablolar.get("gtip_cpc", []):
            gtip, cpc = e.get("gtip"), e.get("cpc")
            if not gtip or not cpc:
                continue
            self.gtip_cpc_idx.setdefault(gtip, []).append(e)
            self.cpc_to_gtip.setdefault(cpc, []).append(gtip)

        for e in tablolar.get("gtip_nace", []):
            gtip, nace = e.get("gtip"), e.get("nace")
            if not gtip or not nace:
                continue
            self.gtip_nace_idx.setdefault(gtip, []).append(e)
            self.nace_to_gtip.setdefault(nace, []).append(gtip)

        for e in tablolar.get("nace_isco", []):
            nace, isco = e.get("nace"), e.get("isco")
            if not nace or not isco:
                continue
            self.nace_isco_idx.setdefault(nace, []).append(e)
            self.nace_to_isco.setdefault(nace, {})[isco] = e
            self.isco_to_nace.setdefault(isco, []).append(nace)

        # Bu görünüm doğrudan NACE–CPC eşleştirmesi değildir; GTİP ortaklığı
        # üzerinden türetilen ilişki olarak açıkça etiketlenir.
        for nace_kod, gtip_kodlari in self.nace_to_gtip.items():
            cpc_map = self.nace_to_cpc.setdefault(nace_kod, {})
            for gtip_kod in gtip_kodlari:
                for e in self.gtip_cpc_idx.get(gtip_kod, []):
                    cpc = e["cpc"]
                    obj = self.cpc_idx.get(cpc) or {}
                    cpc_map[cpc] = {
                        "ref": f"cpc:{cpc}", "kod": cpc,
                        "ad_tr": obj.get("ad_tr"), "ad_en": obj.get("ad_en"),
                        "iliski_turu": "gtip_uzerinden",
                        "iliski_yolu": "nace_gtip_cpc",
                    }

    def _json(self, p: Path):
        return json.load(open(p, encoding="utf-8"))

    def _idx(self, p: Path):
        return {r["kod"]: r for r in self._json(p).get("kayitlar", [])}

    # ─── Eşleşme ─────────────────────────────────────────────────
    def _match(self, kod: str, eslesme: dict) -> tuple[bool, int]:
        if not eslesme:
            return False, 0
        if eslesme.get("tum_urunler"):
            return True, 0
        exact = eslesme.get("exact", [])
        if exact and kod in exact:
            return True, len(kod)
        prefixler = eslesme.get("prefix", [])
        haric     = eslesme.get("haric", [])
        if not prefixler:
            return False, 0
        if haric and any(kod.startswith(h) for h in haric):
            return False, 0
        en_uzun = 0
        for p in prefixler:
            if kod.startswith(p) and len(p) > en_uzun:
                en_uzun = len(p)
        return (True, en_uzun) if en_uzun else (False, 0)

    def _kurallari_bul(self, kod: str, kurallar: list, sistem: str = "gtip"):
        eslesenler = []
        for k in kurallar:
            e = (k.get("eslesmeler") or {}).get(sistem)
            if not e:
                continue
            esl, plen = self._match(kod, e)
            if esl:
                eslesenler.append((k, plen))
        eslesenler.sort(key=lambda x: (x[0].get("oncelik", 0), x[1]), reverse=True)
        return eslesenler

    def _ref_bul(self, eslesenler: list, tip: str):
        for kural, _ in eslesenler:
            refs = kural.get("referanslar") or {}
            if tip in refs:
                return kural, refs[tip]
        return None, None

    # ─── KDV ─────────────────────────────────────────────────────
    def _kdv_hesapla(self, yon: str, eslesenler: list) -> dict:
        for kural, _ in eslesenler:
            islemler = kural.get("islem_turleri") or ["yurtici", "ithalat", "ihracat"]
            if yon not in islemler:
                continue
            kdv_ref = (kural.get("referanslar") or {}).get("kdv")
            if not isinstance(kdv_ref, dict) or "ref" not in kdv_ref:
                continue
            kayit = self.kdv_idx.get(kdv_ref["ref"])
            if not kayit:
                continue
            tur = kayit.get("tur", "oran")
            return {
                "ref":         kdv_ref["ref"],
                "kural":       kural["kod"],
                "tip":         "istisna" if tur == "istisna" else "dogrudan",
                "kaynak_tipi": "kural",
                "oncelik":     kural.get("oncelik", 100),
                "tur":         tur,
                "oran":        kayit.get("oran"),
                "oran_birimi": kayit.get("oran_birimi", "kesir"),
                "gecerlilik":  kayit.get("gecerlilik"),
            }

        fb_kod = (self.vergi_meta.get("fallback") or {}).get("kdv", {}).get(yon)
        if fb_kod:
            kayit = self.kdv_idx.get(fb_kod, {})
            tur = kayit.get("tur", "oran")
            return {
                "ref":         fb_kod,
                "kural":       None,
                "tip":         "istisna" if tur == "istisna" else "fallback",
                "kaynak_tipi": "fallback",
                "oncelik":     0,
                "tur":         tur,
                "oran":        kayit.get("oran"),
                "oran_birimi": kayit.get("oran_birimi", "kesir"),
            }
        return {"ref": "yok", "tip": "yok", "kaynak_tipi": "yok"}

    # ─── ÖTV ─────────────────────────────────────────────────────
    def _otv_hesapla(self, yon: str, eslesenler: list,
                     aday_secilen: Optional[str] = None) -> dict:
        for kural, _ in eslesenler:
            islemler = kural.get("islem_turleri") or ["yurtici", "ithalat", "ihracat"]
            if yon not in islemler:
                continue
            otv_ref = (kural.get("referanslar") or {}).get("otv")
            if not isinstance(otv_ref, dict):
                continue

            if otv_ref.get("parametrik"):
                adaylar = []
                for a in otv_ref.get("adaylar", []):
                    e = (a.get("eslesmeler") or {}).get("gtip")
                    if not e:
                        continue
                    esl, _ = self._match(current_kod, e)
                    if not esl:
                        continue
                    adaylar.append({
                        "ref":              a["ref"],
                        "kosul":            a.get("kosul"),
                        "uygulanabilirlik": a.get("uygulanabilirlik", "secim_bekliyor"),
                    })
                if aday_secilen:
                    kayit = self.otv_idx.get(aday_secilen, {})
                    return {
                        "ref":         aday_secilen,
                        "kural":       kural["kod"],
                        "tip":         "dogrudan",
                        "kaynak_tipi": "kural",
                        "tur":         kayit.get("tur"),
                        "oran":        kayit.get("oran"),
                        "maktu":       kayit.get("maktu"),
                        "adaylar":     adaylar,
                    }
                return {"kural": kural["kod"], "tip": "secim_bekliyor", "adaylar": adaylar}

            if "ref" in otv_ref:
                kayit = self.otv_idx.get(otv_ref["ref"], {})
                return {
                    "ref":          otv_ref["ref"],
                    "kural":        kural["kod"],
                    "tip":          "dogrudan",
                    "kaynak_tipi":  "kural",
                    "tur":          kayit.get("tur"),
                    "oran":         kayit.get("oran"),
                    "maktu":        kayit.get("maktu"),
                    "asgari_maktu": kayit.get("asgari_maktu"),
                    "birim":        kayit.get("maktu_birim"),
                }

        kayit = self.otv_idx.get("otv-yok", {})
        return {
            "ref":         "otv-yok",
            "kural":       None,
            "tip":         "fallback",
            "kaynak_tipi": "fallback",
            "tur":         kayit.get("tur", "yok"),
            "oran":        0,
        }

    # ─── Gümrük ──────────────────────────────────────────────────
    def _gumruk_hesapla(self, kod: str, gv_ref: dict, kural: dict) -> dict:
        kayitlar = self.gumruk_by_kod.get(kod, [])
        if not kayitlar:
            return {
                "ref":              "gumruk-vergisi",
                "kural":            kural.get("kod"),
                "uygulanabilirlik": gv_ref.get("uygulanabilirlik"),
                "listeler":         [],
            }

        sutunlar      = self.gumruk_sema.get("sutunlar", {})
        ulke_gruplari = self.gumruk_sema.get("ulke_gruplari", {})
        listeler = []
        for r in kayitlar:
            liste    = r["liste"]
            gv       = r.get("gv", [])
            kolonlar = sutunlar.get(liste, [])
            oranlar  = []
            for i, oran in enumerate(gv):
                if i >= len(kolonlar):
                    break
                ulke = kolonlar[i]
                ug   = ulke_gruplari.get(ulke, {})
                oranlar.append({
                    "ulke_grubu":  ulke,
                    "ulke_adi_tr": ug.get("tr"),
                    "ulke_adi_en": ug.get("en"),
                    "oran":        oran,
                })
            listeler.append({"liste": liste, "oranlar": oranlar})

        return {
            "ref":              "gumruk-vergisi",
            "kural":            kural.get("kod"),
            "oran_birimi":      self.gumruk_sema.get("oran_birimi", "ondalik"),
            "uygulanabilirlik": gv_ref.get("uygulanabilirlik"),
            "listeler":         listeler,
        }

    # ─── IGV / Tevkifat ──────────────────────────────────────────
    def _igv_hesapla(self, igv_ref: dict, kural: dict) -> Optional[dict]:
        if not isinstance(igv_ref, dict) or "ref" not in igv_ref:
            return None
        kayit = self.igv_idx.get(igv_ref["ref"])
        if not kayit:
            return None
        return {
            "ref":         igv_ref["ref"],
            "kural":       kural["kod"],
            "mense_grubu": kayit.get("mense_grubu"),
            "tur":         kayit.get("tur"),
            "oran":        kayit.get("oran"),
            "oran_birimi": "kesir",
        }

    def _tevkifat_hesapla(self, tv_ref: dict, kural: dict) -> Optional[dict]:
        if not isinstance(tv_ref, dict) or "ref" not in tv_ref:
            return None
        kayit = self.tevkifat_idx.get(tv_ref["ref"])
        if not kayit:
            return None
        return {
            "ref":              tv_ref["ref"],
            "kural":            kural["kod"],
            "tur":              kayit.get("tur"),
            "oran":             kayit.get("oran"),
            "islem_kategorisi": kayit.get("islem_kategorisi"),
        }

    # ─── Vergi orkestrasyon ──────────────────────────────────────
    def vergi_hesapla(self, kod: str, aday_secilen: Optional[str] = None) -> dict:
        global current_kod
        current_kod = kod
        eslesenler = self._kurallari_bul(kod, self.vergi_kurallari)

        sonuc = {
            "kdv": {},
            "otv": {},
            "gumruk_vergisi": {},
            "ilave_gumruk_vergisi": {},
            "tevkifat": {},
        }

        for yon in ("yurtici", "ithalat", "ihracat"):
            sonuc["kdv"][yon] = self._kdv_hesapla(yon, eslesenler)
            sonuc["otv"][yon] = self._otv_hesapla(yon, eslesenler, aday_secilen)

        _, gv_ref = self._ref_bul(eslesenler, "gumruk-vergisi")
        if gv_ref:
            for kural, _ in eslesenler:
                if "gumruk-vergisi" in (kural.get("referanslar") or {}):
                    sonuc["gumruk_vergisi"]["ithalat"] = self._gumruk_hesapla(
                        kod, gv_ref, kural
                    )
                    break

        _, igv_ref = self._ref_bul(eslesenler, "ilave-gumruk-vergisi")
        if igv_ref:
            for kural, _ in eslesenler:
                if "ilave-gumruk-vergisi" in (kural.get("referanslar") or {}):
                    igv = self._igv_hesapla(igv_ref, kural)
                    if igv:
                        sonuc["ilave_gumruk_vergisi"]["ithalat"] = igv
                    break

        _, tv_ref = self._ref_bul(eslesenler, "tevkifat")
        if tv_ref:
            for kural, _ in eslesenler:
                if "tevkifat" in (kural.get("referanslar") or {}):
                    tv = self._tevkifat_hesapla(tv_ref, kural)
                    if tv:
                        sonuc["tevkifat"]["yurtici"] = tv
                    break

        return sonuc

    # ─── Belgeler ────────────────────────────────────────────────
    def _belge_kayitlari(self, eslesenler: list, alan: str = "belgeler") -> list:
        gorulen = {}
        for eslesen in eslesenler:
            kural, _, kaynak_kod = (eslesen if len(eslesen) == 3
                                    else (*eslesen, None))
            oncelik = kural.get("oncelik", 100)
            for b in kural.get(alan, []):
                ref = b.get("ref")
                if not ref:
                    continue
                if ref not in gorulen or oncelik > gorulen[ref]["oncelik"]:
                    gorulen[ref] = {
                        "b": b, "oncelik": oncelik, "kural": kural,
                        "kaynak_kodlari": set([kaynak_kod]) if kaynak_kod else set(),
                    }
                elif oncelik == gorulen[ref]["oncelik"] and kaynak_kod:
                    gorulen[ref]["kaynak_kodlari"].add(kaynak_kod)

        sonuc = []
        for ref, veri in gorulen.items():
            b      = veri["b"]
            master = self.belge_master.get(ref, {})
            ad_tr  = master.get("ad_tr") or ref
            ad_en  = master.get("ad_en") or ref

            durum = b.get("uygulanabilirlik") or "opsiyonel"
            if durum == "zorunlu" or b.get("zorunlu") is True:
                durum = "zorunlu"
            elif durum == "kosullu":
                durum = "kosullu"
            else:
                durum = "opsiyonel"

            kayit = {
                "kod":     ref,
                "ad_tr":   ad_tr,
                "ad_en":   ad_en,
                "durum":   durum,
                "kural":   veri["kural"]["kod"],
                "oncelik": veri["oncelik"],
                "yon":     b.get("yon") or ["yurtici"],
            }
            if veri["kaynak_kodlari"]:
                kayit["kaynak_kodlari"] = sorted(veri["kaynak_kodlari"])
            if b.get("kapsam"):
                kayit["kapsam"] = b["kapsam"]
            if b.get("kosul"):
                kayit["kosul"] = {"tr": b["kosul"], "en": b["kosul"]}
            sonuc.append(kayit)
        return sorted(sonuc, key=lambda x: (x["oncelik"], x["kod"]), reverse=True)

    @staticmethod
    def _belge_gruplari(kayitlar: list) -> dict:
        gruplar = {"yurtici": [], "ithalat": [], "ihracat": []}
        for kayit in kayitlar:
            for yon in kayit.get("yon", ["yurtici"]):
                if yon in gruplar:
                    gruplar[yon].append(dict(kayit))
        return gruplar

    def belge_hesapla(self, kod: str) -> dict:
        eslesenler = self._kurallari_bul(kod, self.belge_kurallari, "gtip")
        return self._belge_gruplari(self._belge_kayitlari(eslesenler))

    def faaliyet_belgeleri_hesapla(self, nace_kodlari: list) -> list:
        eslesenler = []
        for nace_kod in nace_kodlari:
            for kural, uzunluk in self._kurallari_bul(
                    nace_kod, self.faaliyet_belge_kurallari, "nace"):
                eslesenler.append((kural, uzunluk, nace_kod))
        kayitlar = self._belge_kayitlari(eslesenler)
        for kayit in kayitlar:
            kayit["iliski_yolu"] = "gtip_nace_faaliyet_belgesi"
        return kayitlar

    def mesleki_belgeler_hesapla(self, isco_kod: str) -> list:
        eslesenler = self._kurallari_bul(
            isco_kod, self.meslek_belge_kurallari, "isco")
        return self._belge_kayitlari(eslesenler, "mesleki_belgeler")

    # ─── İlişkiler ───────────────────────────────────────────────
    @staticmethod
    def _kod_gorunumu(katalog: dict, sistem: str, kod: str) -> dict:
        kayit = katalog.get(kod) or {}
        return {
            "ref": f"{sistem}:{kod}",
            "kod": kod,
            "ad_tr": kayit.get("ad_tr"),
            "ad_en": kayit.get("ad_en"),
        }

    def _isco_gorunumu(self, nace_kod: str, edge: dict) -> dict:
        kod = edge["isco"]
        sonuc = self._kod_gorunumu(self.isco_idx, "isco", kod)
        sonuc.update({
            "kaynak": f"nace:{nace_kod}",
            "kaynak_nace": nace_kod,
            "kural_ref": edge.get("kural_ref"),
            "iliski_turu": edge.get("iliski_turu"),
            "iliski_yolu": "gtip_nace_isco",
        })
        return sonuc

    def iliski_hesapla(self, kod: str) -> dict:
        nace_edges = self.gtip_nace_idx.get(kod, [])
        cpc_edges = self.gtip_cpc_idx.get(kod, [])
        nace_kodlari = [e["nace"] for e in nace_edges]
        isco = {}
        for nace_kod in nace_kodlari:
            for edge in self.nace_isco_idx.get(nace_kod, []):
                # Aynı mesleğe birden fazla NACE yolu varsa her yol izlenebilir kalsın.
                isco[(edge["isco"], nace_kod)] = self._isco_gorunumu(nace_kod, edge)
        return {
            "nace": [
                {**self._kod_gorunumu(self.nace_idx, "nace", e["nace"]),
                 "iliski_turu": e.get("iliski_turu")}
                for e in nace_edges
            ],
            "cpc": [
                {**self._kod_gorunumu(self.cpc_idx, "cpc", e["cpc"]),
                 "iliski_turu": e.get("iliski_turu")}
                for e in cpc_edges
            ],
            "isco": sorted(isco.values(), key=lambda x: (x["kod"], x["kaynak_nace"])),
        }

    # ─── GTİP konsolide (tek kayıt) ──────────────────────────────
    def konsolide_et(self, kod: str, aday_secilen: Optional[str] = None) -> dict:
        gtip = self.gtip_idx.get(kod)
        if not gtip:
            raise ValueError(f"GTİP bulunamadı: {kod}")
        if not gtip.get("yaprak"):
            raise ValueError(f"GTİP yaprak değil (seviye {gtip.get('seviye')}): {kod}")

        iliski = self.iliski_hesapla(kod)
        vergi  = self.vergi_hesapla(kod, aday_secilen)
        belge  = self.belge_hesapla(kod)

        return {
            "kod":         kod,
            "ust_kod":     gtip.get("ust_kod"),
            "seviye":      int(gtip.get("seviye") or 6),
            "yaprak":      bool(gtip.get("yaprak")),
            "ad_tr":       gtip.get("ad_tr"),
            "ad_en":       gtip.get("ad_en"),
            "olcu_birimi": gtip.get("olcu_birimi"),
            "vergi":       vergi,
            "belgeler":    belge,
            "cpc":         iliski["cpc"],
            "nace":        iliski["nace"],
            "isco":        iliski["isco"],
        }

    # ─── CPC konsolide (tek kayıt) ───────────────────────────────
    def cpc_konsolide_et(self, cpc_kod: str) -> dict:
        cpc = self.cpc_idx.get(cpc_kod)
        if not cpc:
            raise ValueError(f"CPC bulunamadı: {cpc_kod}")
        if not cpc.get("yaprak"):
            raise ValueError(f"CPC yaprak değil (seviye {cpc.get('seviye')}): {cpc_kod}")

        gtip_kodlari = self.cpc_to_gtip.get(cpc_kod, [])

        gtipler = []
        for gkod in gtip_kodlari:
            g = self.gtip_idx.get(gkod)
            if g:
                gtipler.append({
                    "ref":   f"gtip:{gkod}",
                    "kod":   gkod,
                    "ad_tr": g.get("ad_tr"),
                    "ad_en": g.get("ad_en"),
                })
        gtipler.sort(key=lambda x: x["kod"])

        nace_map = {}
        isco_map = {}
        for gkod in gtip_kodlari:
            for edge in self.gtip_nace_idx.get(gkod, []):
                nkod = edge["nace"]
                obj = self._kod_gorunumu(self.nace_idx, "nace", nkod)
                obj.update({"iliski_turu": edge.get("iliski_turu"),
                            "iliski_yolu": "cpc_gtip_nace"})
                nace_map[nkod] = obj
                for iedge in self.nace_isco_idx.get(nkod, []):
                    iobj = self._isco_gorunumu(nkod, iedge)
                    iobj["iliski_yolu"] = "cpc_gtip_nace_isco"
                    isco_map[(iedge["isco"], nkod)] = iobj

        return {
            "kod":     cpc_kod,
            "ust_kod": cpc.get("ust_kod"),
            "seviye":  int(cpc.get("seviye") or 5),
            "yaprak":  bool(cpc.get("yaprak")),
            "ad_tr":   cpc.get("ad_tr"),
            "ad_en":   cpc.get("ad_en"),
            "gtip":    gtipler,
            "nace":    sorted(nace_map.values(), key=lambda x: x["kod"]),
            "isco":    sorted(isco_map.values(), key=lambda x: x["kod"]),
        }

    # ─── NACE konsolide (tek kayıt) ──────────────────────────────
    def nace_konsolide_et(self, nace_kod: str) -> dict:
        nace = self.nace_idx.get(nace_kod)
        if not nace:
            raise ValueError(f"NACE bulunamadı: {nace_kod}")

        gtip_kodlari = self.nace_to_gtip.get(nace_kod, [])

        gtipler = []
        for gkod in gtip_kodlari:
            g = self.gtip_idx.get(gkod)
            if g:
                gtipler.append({
                    "ref":   f"gtip:{gkod}",
                    "kod":   gkod,
                    "ad_tr": g.get("ad_tr"),
                    "ad_en": g.get("ad_en"),
                })
        gtipler.sort(key=lambda x: x["kod"])

        isco_map = {
            kod: self._isco_gorunumu(nace_kod, edge)
            for kod, edge in self.nace_to_isco.get(nace_kod, {}).items()
        }
        cpc_map  = self.nace_to_cpc.get(nace_kod, {})
        faaliyet_belgeleri = self._belge_kayitlari(
            self._kurallari_bul(nace_kod, self.faaliyet_belge_kurallari, "nace")
        )
        for kayit in faaliyet_belgeleri:
            kayit["iliski_yolu"] = "nace_faaliyet_belgesi"

        return {
            "kod":     nace_kod,
            "ust_kod": nace.get("ust_kod"),
            "seviye":  int(nace.get("seviye") or 4),
            "yaprak":  bool(nace.get("yaprak")),
            "ad_tr":   nace.get("ad_tr"),
            "ad_en":   nace.get("ad_en"),
            "gtip":    gtipler,
            "cpc":     sorted(cpc_map.values(), key=lambda x: x["kod"]),
            "isco":    sorted(isco_map.values(), key=lambda x: x["kod"]),
            "faaliyet_belgeleri": faaliyet_belgeleri,
        }

    def isco_konsolide_et(self, isco_kod: str) -> dict:
        isco = self.isco_idx.get(isco_kod)
        if not isco:
            raise ValueError(f"ISCO bulunamadı: {isco_kod}")
        nace_kodlari = sorted(set(self.isco_to_nace.get(isco_kod, [])))

        nace_kayitlari = []
        gtip_map = {}
        nace_edges = {
            e["nace"]: e
            for nace_kod in nace_kodlari
            for e in self.nace_isco_idx.get(nace_kod, [])
            if e["isco"] == isco_kod
        }
        for nace_kod in nace_kodlari:
            edge = nace_edges[nace_kod]
            nace_obj = self._kod_gorunumu(self.nace_idx, "nace", nace_kod)
            nace_obj.update({"iliski_turu": edge.get("iliski_turu"),
                             "kural_ref": edge.get("kural_ref"),
                             "iliski_yolu": "nace_isco"})
            nace_kayitlari.append(nace_obj)

            for gtip_kod in self.nace_to_gtip.get(nace_kod, []):
                if gtip_kod not in gtip_map:
                    gtip_obj = self._kod_gorunumu(self.gtip_idx, "gtip", gtip_kod)
                    gtip_obj.update({"kaynak_nace_kodlari": [],
                                     "iliski_yolu": "gtip_nace_isco"})
                    gtip_map[gtip_kod] = gtip_obj
                gtip_map[gtip_kod]["kaynak_nace_kodlari"].append(nace_kod)

        for gtip_obj in gtip_map.values():
            gtip_obj["kaynak_nace_kodlari"] = sorted(set(gtip_obj["kaynak_nace_kodlari"]))

        return {
            "kod": isco_kod,
            "ust_kod": isco.get("ust_kod"),
            "seviye": int(isco.get("seviye") or 4),
            "yaprak": bool(isco.get("yaprak")),
            "ad_tr": isco.get("ad_tr"),
            "ad_en": isco.get("ad_en"),
            "nace": nace_kayitlari,
            "gtip": sorted(gtip_map.values(), key=lambda x: x["kod"]),
            "mesleki_belgeler": self.mesleki_belgeler_hesapla(isco_kod),
        }


# ══════════════════════════════════════════════════════════════════
# Toplu üretim
# ══════════════════════════════════════════════════════════════════
def temizle_eski():
    if KONSOLIDE.exists():
        shutil.rmtree(KONSOLIDE)
    KONSOLIDE.mkdir(parents=True, exist_ok=True)
    if KATALOG_DOSYA.exists():
        KATALOG_DOSYA.unlink()


def toplu_uret(motor: KuralMotoru, limit=0, fasil=None) -> tuple[list, int]:
    yapraklar = [
        kod for kod, r in motor.gtip_idx.items()
        if r.get("yaprak") and (fasil is None or kod.startswith(fasil))
    ]
    yapraklar.sort()
    if limit:
        yapraklar = yapraklar[:limit]

    print(f"→ {len(yapraklar)} GTİP yaprağı üretilecek\n")
    bas = time.time()
    kayitlar = []
    hata = 0
    for i, kod in enumerate(yapraklar, 1):
        try:
            kayitlar.append(motor.konsolide_et(kod))
            if i % 2000 == 0 or i == len(yapraklar):
                gecen = time.time() - bas
                hiz = i / gecen if gecen else 0
                print(f"  [{i:5d}/{len(yapraklar)}] ({hiz:.0f}/s, {gecen:.0f}s)")
        except Exception as e:
            hata += 1
            print(f"  ❌ {kod}: {e}")
    return kayitlar, hata


def toplu_uretcpc(motor: KuralMotoru, limit: int = 0) -> tuple[list, int]:
    yapraklar = [kod for kod, r in motor.cpc_idx.items() if r.get("yaprak")]
    yapraklar.sort()
    if limit:
        yapraklar = yapraklar[:limit]

    print(f"→ {len(yapraklar)} CPC yaprağı üretilecek\n")
    bas = time.time()
    kayitlar = []
    hata = 0
    for i, kod in enumerate(yapraklar, 1):
        try:
            kayitlar.append(motor.cpc_konsolide_et(kod))
            if i % 1000 == 0 or i == len(yapraklar):
                gecen = time.time() - bas
                hiz = i / gecen if gecen else 0
                print(f"  [{i:5d}/{len(yapraklar)}] ({hiz:.0f}/s, {gecen:.0f}s)")
        except Exception as e:
            hata += 1
            print(f"  ❌ {kod}: {e}")
    return kayitlar, hata


def toplu_uretnace(motor: KuralMotoru, limit: int = 0) -> tuple[list, int]:
    kodlar = sorted(motor.nace_idx)
    if limit:
        kodlar = kodlar[:limit]

    print(f"→ {len(kodlar)} NACE kodu üretilecek\n")
    bas = time.time()
    kayitlar = []
    hata = 0
    for i, kod in enumerate(kodlar, 1):
        try:
            kayitlar.append(motor.nace_konsolide_et(kod))
            if i % 1000 == 0 or i == len(kodlar):
                gecen = time.time() - bas
                hiz = i / gecen if gecen else 0
                print(f"  [{i:5d}/{len(kodlar)}] ({hiz:.0f}/s, {gecen:.0f}s)")
        except Exception as e:
            hata += 1
            print(f"  ❌ {kod}: {e}")
    return kayitlar, hata


def toplu_uretisco(motor: KuralMotoru, limit: int = 0) -> tuple[list, int]:
    kodlar = sorted(kod for kod, r in motor.isco_idx.items() if r.get("yaprak"))
    if limit:
        kodlar = kodlar[:limit]

    print(f"→ {len(kodlar)} ISCO yaprağı üretilecek\n")
    bas = time.time()
    kayitlar = []
    hata = 0
    for i, kod in enumerate(kodlar, 1):
        try:
            kayitlar.append(motor.isco_konsolide_et(kod))
            if i % 200 == 0 or i == len(kodlar):
                gecen = time.time() - bas
                hiz = i / gecen if gecen else 0
                print(f"  [{i:5d}/{len(kodlar)}] ({hiz:.0f}/s, {gecen:.1f}s)")
        except Exception as e:
            hata += 1
            print(f"  ❌ {kod}: {e}")
    return kayitlar, hata


def _meta_yaz(kayitlar: list, schema: str, servis: str, kapsam: str,
              limit: int, fasil: Optional[str]) -> dict:
    yapi = {
        "tip":          "liste",
        "kayit_sayisi": len(kayitlar),
        "limit":        limit or None,
    }
    if fasil is not None:
        yapi["fasil"] = fasil

    kapsam_adi = {"nace": "faaliyet", "isco": "meslek"}.get(kapsam, "urun")
    adlar = {
        "gtip-konsolide": ("Konsolide GTİP Kodları", "Consolidated Turkish Customs Tariff Codes"),
        "cpc-konsolide": ("Konsolide CPC Kodları", "Consolidated Central Product Classification Codes"),
        "nace-konsolide": ("Konsolide NACE Faaliyet Kodları", "Consolidated NACE Activity Codes"),
        "isco-konsolide": ("Konsolide ISCO Meslek Kodları", "Consolidated ISCO Occupation Codes"),
    }
    ad_tr, ad_en = adlar[servis]
    return {
        "schema": schema,
        "surum": RELEASE["surum"],
        "kod": servis,
        "ad_tr": ad_tr,
        "ad_en": ad_en,
        "tarih": RELEASE["tarih"],
        "guncelleme": RELEASE["guncelleme"],
        "durum": RELEASE["durum"],
        "katman": "konsolide",
        "kapsam": [kapsam_adi],
        "islem_turleri": [],
        "yayinci": "pdaas",
        "sorumlu_kurum": "pdaas",
        "kaynaklar_ref": "meta/kaynaklar.json",
        "mevzuat_ref": "meta/mevzuat.json",
        "sozluk_ref": "meta/sozluk.json",
        "gecerlilik": {"baslangic": "2026-01-01", "bitis": None},
        "kayit_sayisi": len(kayitlar),
        "detay": {
            "yapi": yapi,
            "katalog_ref": {"dosya": "meta/katalog.json"},
        },
        "checksum": None,
    }


def tek_dosya_yaz(kayitlar: list, limit: int = 0, fasil: str = None) -> Path:
    meta = _meta_yaz(kayitlar, "gtip-konsolide/v1", "gtip-konsolide",
                     "gtip", limit, fasil)
    HEDEF_DOSYA.parent.mkdir(parents=True, exist_ok=True)
    json_yaz(HEDEF_DOSYA, {"meta": meta, "kayitlar": kayitlar})
    return HEDEF_DOSYA


def cpc_tek_dosya_yaz(kayitlar: list, limit: int = 0) -> Path:
    meta = _meta_yaz(kayitlar, "cpc-konsolide/v1", "cpc-konsolide",
                     "cpc", limit, None)
    CPC_HEDEF_DOSYA.parent.mkdir(parents=True, exist_ok=True)
    json_yaz(CPC_HEDEF_DOSYA, {"meta": meta, "kayitlar": kayitlar})
    return CPC_HEDEF_DOSYA


def nace_tek_dosya_yaz(kayitlar: list, limit: int = 0) -> Path:
    meta = _meta_yaz(kayitlar, "nace-konsolide/v1", "nace-konsolide",
                     "nace", limit, None)
    NACE_HEDEF_DOSYA.parent.mkdir(parents=True, exist_ok=True)
    json_yaz(NACE_HEDEF_DOSYA, {"meta": meta, "kayitlar": kayitlar})
    return NACE_HEDEF_DOSYA


def isco_tek_dosya_yaz(kayitlar: list, limit: int = 0) -> Path:
    meta = _meta_yaz(kayitlar, "isco-konsolide/v1", "isco-konsolide",
                     "isco", limit, None)
    ISCO_HEDEF_DOSYA.parent.mkdir(parents=True, exist_ok=True)
    json_yaz(ISCO_HEDEF_DOSYA, {"meta": meta, "kayitlar": kayitlar})
    return ISCO_HEDEF_DOSYA


# ══════════════════════════════════════════════════════════════════
# meta/katalog.json
# ══════════════════════════════════════════════════════════════════
def _varlik(p: Path, tip: str) -> dict:
    d = json.load(open(p, encoding="utf-8"))
    meta = d.get("meta", {})
    return {
        "kod": meta.get("kod"),
        "ad_tr": meta.get("ad_tr"),
        "ad_en": meta.get("ad_en"),
        "schema": meta.get("schema"),
        "surum": meta.get("surum"),
        "tarih": meta.get("tarih"),
        "guncelleme": meta.get("guncelleme"),
        "dosya": p.relative_to(V1).as_posix(),
        "tip": tip,
        "boyut_byte": p.stat().st_size,
        "kayit_sayisi": meta.get("kayit_sayisi", kayit_sayisini_bul(d)),
        "durum": meta.get("durum"),
        "checksum": meta.get("checksum") or json_checksum(d),
    }


def katalog_uret() -> dict:
    varliklar = {"ham": [], "belge": [], "kural": [], "iliskiler": [],
                 "konsolide": [], "meta": [], "ornek": []}

    for p in sorted(HAM.glob("*.json")):
        tip = "ornek" if p.name.endswith("-meta-ornek.json") else "ham"
        varliklar[tip].append(_varlik(p, tip))
    for p in sorted(BELGE.glob("*.json")):
        varliklar["belge"].append(_varlik(p, "belge"))
    for p in sorted(KURAL.glob("*.json")):
        tip = "ornek" if p.name.endswith("-meta-ornek.json") else (
            "iliskiler" if p.stem == "kod-iliskileri" else "kural")
        varliklar[tip].append(_varlik(p, tip))
    for hedef in (HEDEF_DOSYA, CPC_HEDEF_DOSYA, NACE_HEDEF_DOSYA, ISCO_HEDEF_DOSYA):
        if hedef.exists():
            varliklar["konsolide"].append(_varlik(hedef, "konsolide"))
    for p in sorted(META.glob("*.json")):
        if p.name in {"katalog.json", "manifest.json"}:
            continue
        if p.name.endswith("-meta-ornek.json"):
            varliklar["ornek"].append(_varlik(p, "ornek"))
        else:
            varliklar["meta"].append(_varlik(p, "sozlesme"))

    istatistikler = {
        "ham_dosya": len(varliklar["ham"]),
        "belge_dosya": len(varliklar["belge"]),
        "kural_dosya": len(varliklar["kural"]) + len(varliklar["iliskiler"]),
        "ham_kayit": sum(v["kayit_sayisi"] for v in varliklar["ham"]),
        "belge_kayit": sum(v["kayit_sayisi"] for v in varliklar["belge"]),
        "kural_kayit": sum(v["kayit_sayisi"] for v in varliklar["kural"] + varliklar["iliskiler"]),
        "konsolide_set": len(varliklar["konsolide"]),
        "ornek_dosya": len(varliklar["ornek"]),
    }
    katalog = {
        "meta": {
            "schema": "katalog/v1", "surum": RELEASE["surum"], "kod": "katalog",
            "ad_tr": "PDaaS Veri Kataloğu", "ad_en": "PDaaS Data Catalog",
            "tarih": RELEASE["tarih"], "guncelleme": RELEASE["guncelleme"],
            "durum": RELEASE["durum"], "katman": "sozlesme", "kapsam": [],
            "islem_turleri": [], "yayinci": "pdaas", "sorumlu_kurum": "pdaas",
            "kaynaklar_ref": None, "mevzuat_ref": None, "sozluk_ref": "meta/sozluk.json",
            "gecerlilik": {"baslangic": "2026-01-01", "bitis": None},
            "checksum": None,
            "kayit_sayisi": sum(v["kayit_sayisi"] for group in varliklar.values() for v in group),
            "detay": {},
        },
        "varliklar": varliklar,
        "istatistikler": istatistikler,
    }
    json_yaz(KATALOG_DOSYA, katalog)
    return istatistikler


def manifest_uret() -> dict:
    def liste(klasor: Path, tip: str) -> list:
        if not klasor.exists():
            return []
        return [{
            "dosya": p.relative_to(V1).as_posix(),
            "checksum": _varlik(p, tip)["checksum"],
            "boyut": p.stat().st_size,
            "kayit_sayisi": kayit_sayisini_bul(json.load(open(p, encoding="utf-8"))),
        } for p in sorted(klasor.glob("*.json"))]

    kaynaklar = {
        "ham": [x for x in liste(HAM, "ham") if not x["dosya"].endswith("-meta-ornek.json")],
        "belge": liste(BELGE, "belge"),
        "kural": [x for x in liste(KURAL, "kural") if not x["dosya"].endswith("-meta-ornek.json")],
        "konsolide": liste(KONSOLIDE, "konsolide"),
        "meta": [x for x in liste(META, "sozlesme")
                 if Path(x["dosya"]).name not in {"katalog.json", "manifest.json"}
                 and not Path(x["dosya"]).name.endswith("-meta-ornek.json")],
    }
    kaynaklar["ornek"] = [x for group, folder in (("ham", HAM), ("kural", KURAL), ("sozlesme", META))
                          for x in liste(folder, group) if x["dosya"].endswith("-meta-ornek.json")]
    katalog = _varlik(KATALOG_DOSYA, "sozlesme") if KATALOG_DOSYA.exists() else None
    cikti = {"dosyalar": kaynaklar["konsolide"], "katalog": katalog}
    istatistikler = {
        "ham_dosya": len(kaynaklar["ham"]),
        "belge_dosya": len(kaynaklar["belge"]),
        "kural_dosya": len(kaynaklar["kural"]),
        "konsolide_dosya": len(kaynaklar["konsolide"]),
        "kayit_sayisi": sum(x["kayit_sayisi"] for group in kaynaklar.values() for x in group),
    }
    manifest = {
        "meta": {
            "schema": "manifest/v1", "surum": RELEASE["surum"], "kod": "manifest",
            "ad_tr": "PDaaS Derleme Manifesti", "ad_en": "PDaaS Build Manifest",
            "tarih": RELEASE["tarih"], "guncelleme": RELEASE["guncelleme"],
            "durum": RELEASE["durum"], "katman": "sozlesme", "kapsam": [],
            "islem_turleri": [], "yayinci": "pdaas", "sorumlu_kurum": "pdaas",
            "kaynaklar_ref": None, "mevzuat_ref": None, "sozluk_ref": "meta/sozluk.json",
            "gecerlilik": {"baslangic": "2026-01-01", "bitis": None},
            "checksum": None, "kayit_sayisi": sum(istatistikler.values()),
            "detay": {"uretim": datetime.now(timezone.utc).isoformat()},
        },
        "kaynaklar": kaynaklar,
        "cikti": cikti,
        "istatistikler": istatistikler,
    }
    json_yaz(META / "manifest.json", manifest)
    return istatistikler


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════
def _test():
    motor = KuralMotoru()
    testler = [
        "040320110012", "870322101000", "240220100000",
        "720110110000", "220300010000",
    ]
    for kod in testler:
        try:
            r = motor.konsolide_et(kod)
            kdv = r["vergi"]["kdv"]["yurtici"]
            otv = r["vergi"]["otv"]["yurtici"]
            tv  = r["vergi"].get("tevkifat", {}).get("yurtici", {})
            blg = sum(len(v) for v in r["belgeler"].values())
            print(f"✓ {kod} | KDV: {kdv.get('oran')} ({kdv.get('ref')}) | "
                  f"ÖTV: {otv.get('tur') or otv.get('tip')} | "
                  f"tevkifat: {tv.get('oran')} | belge: {blg}")
        except Exception as e:
            print(f"❌ {kod} — {e}")


def main():
    args = sys.argv[1:]

    if "--test" in args:
        _test()
        return

    if "--meta-only" in args:
        print("╔══ Ortak meta alanları güncelleniyor ═══════════════════")
        result = tum_surumleri_guncelle(
            force="--force" in args or RELEASE.get("force_all", False),
            kuru="--kuru" in args,
            include_consolidated=True,
        )
        print(f"  ✓ {len(result['guncellenen'])} dosya sürüm, tarih ve checksum aldı")
        if result["hata"]:
            print(f"  ❌ {len(result['hata'])} dosya okunamadı")
        if "--kuru" in args:
            return
        katalog_uret()
        manifest_uret()
        print("  ✓ katalog.json ve manifest.json yenilendi")
        return

    tek_kod = next((a for a in args if not a.startswith("--")), None)
    if tek_kod:
        motor = KuralMotoru()
        print(json.dumps(motor.konsolide_et(tek_kod), ensure_ascii=False, indent=2))
        return

    limit    = 0
    fasil    = None
    atla_sil = "--atla-sil" in args
    for i, a in enumerate(args):
        if a == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
        if a == "--fasil" and i + 1 < len(args):
            fasil = args[i + 1]

    # ─── 0. Sürüm güncellemesi ───────────────────────────────
    if "--surum-atla" not in args:
        print("╔══ 0. Tüm dosyaların sürümleri güncelleniyor ══════════")
        r = tum_surumleri_guncelle(
            force="--force" in args or RELEASE.get("force_all", False),
            kuru="--kuru" in args,
        )
        print(f"  ✓ {len(r['guncellenen'])} dosya güncellendi → "
              f"surum={RELEASE['surum']}, tarih={RELEASE['tarih']}, "
              f"guncelleme={RELEASE['guncelleme']}")
        if r["atlanan"]:
            print(f"  ⚠️  {len(r['atlanan'])} dosya atlandı "
                  f"(farklı sürüm, --force ile zorla):")
            for ad, sv in r["atlanan"][:10]:
                print(f"      {ad} (surum={sv})")
        if r["hata"]:
            print(f"  ❌ {len(r['hata'])} hata")
        print()
        if "--kuru" in args:
            print("══ --kuru modu: başka adım çalıştırılmadı ══")
            return

    # ─── 1. Temizlik ─────────────────────────────────────────
    print("╔══ 1. Eski çıktı temizleniyor ══════════════════════════")
    if atla_sil:
        print("  (--atla-sil: atlandı)")
    else:
        temizle_eski()
        print("  ✓ temizlendi")

    motor = KuralMotoru()

    # ─── 2. GTİP konsolide ───────────────────────────────────
    print("\n╔══ 2. GTİP konsolide kayıtlar üretiliyor ═══════════════")
    t0 = time.time()
    kayitlar, hata = toplu_uret(motor, limit, fasil)
    print(f"\n  ✓ {len(kayitlar)} kayıt, {hata} hata, {time.time()-t0:.1f}s")

    # ─── 2.5. CPC konsolide ──────────────────────────────────
    print("\n╔══ 2.5. CPC konsolide kayıtlar üretiliyor ══════════════")
    t0 = time.time()
    cpc_kayitlar, cpc_hata = toplu_uretcpc(motor, limit)
    print(f"\n  ✓ {len(cpc_kayitlar)} kayıt, {cpc_hata} hata, {time.time()-t0:.1f}s")

    # ─── 2.6. NACE konsolide ─────────────────────────────────
    print("\n╔══ 2.6. NACE konsolide kayıtlar üretiliyor ═════════════")
    t0 = time.time()
    nace_kayitlar, nace_hata = toplu_uretnace(motor, limit)
    print(f"\n  ✓ {len(nace_kayitlar)} kayıt, {nace_hata} hata, {time.time()-t0:.1f}s")

    # ─── 2.7. ISCO konsolide ──────────────────────────────────
    print("\n╔══ 2.7. ISCO konsolide kayıtlar üretiliyor ═════════════")
    t0 = time.time()
    isco_kayitlar, isco_hata = toplu_uretisco(motor, limit)
    print(f"\n  ✓ {len(isco_kayitlar)} kayıt, {isco_hata} hata, {time.time()-t0:.1f}s")

    # ─── 4. GTİP konsolide dosyası ───────────────────────────
    print("\n╔══ 4. konsolide/gtip-konsolide.json yazılıyor ══════════")
    t0 = time.time()
    tek_dosya_yaz(kayitlar, limit, fasil)
    print(f"  ✓ {HEDEF_DOSYA.stat().st_size/1e6:.1f} MB, {time.time()-t0:.1f}s")

    # ─── 4.5. CPC konsolide dosyası ──────────────────────────
    print("\n╔══ 4.5. konsolide/cpc-konsolide.json yazılıyor ═════════")
    t0 = time.time()
    cpc_tek_dosya_yaz(cpc_kayitlar, limit)
    print(f"  ✓ {CPC_HEDEF_DOSYA.stat().st_size/1e6:.1f} MB, {time.time()-t0:.1f}s")

    # ─── 4.6. NACE konsolide dosyası ─────────────────────────
    print("\n╔══ 4.6. konsolide/nace-konsolide.json yazılıyor ════════")
    t0 = time.time()
    nace_tek_dosya_yaz(nace_kayitlar, limit)
    print(f"  ✓ {NACE_HEDEF_DOSYA.stat().st_size/1e6:.1f} MB, {time.time()-t0:.1f}s")

    # ─── 4.7. ISCO konsolide dosyası ──────────────────────────
    print("\n╔══ 4.7. konsolide/isco-konsolide.json yazılıyor ════════")
    t0 = time.time()
    isco_tek_dosya_yaz(isco_kayitlar, limit)
    print(f"  ✓ {ISCO_HEDEF_DOSYA.stat().st_size/1e6:.1f} MB, {time.time()-t0:.1f}s")

    # ─── 5. Katalog ve manifest (çıktılar tamamlandıktan sonra) ─
    print("\n╔══ 5. katalog ve manifest güncelleniyor ═══════════════")
    t0 = time.time()
    ist = katalog_uret()
    manifest_uret()
    print(f"  ✓ {ist['ham_dosya']} ham + {ist['belge_dosya']} belge + "
          f"{ist['kural_dosya']} kural + {ist['konsolide_set']} konsolide, "
          f"{time.time()-t0:.1f}s")

    print("\n╔══ BİTTİ ═══════════════════════════════════════════════")
    print(f"  → konsolide/gtip-konsolide.json")
    print(f"  → konsolide/cpc-konsolide.json")
    print(f"  → konsolide/nace-konsolide.json")
    print(f"  → konsolide/isco-konsolide.json")
    print(f"  → meta/katalog.json")
    print(f"  → meta/manifest.json")


if __name__ == "__main__":
    main()
