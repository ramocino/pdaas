#!/usr/bin/env python3
"""PDaaS yayın klasörü doğrulama ve hazırlama aracı.

Kullanım:
    python dogrula.py                    # api/v1'i bulur; doğrular + hazırlar
    python dogrula.py --sadece-dogrula   # yalnızca denetler, hiçbir dosya yazmaz
    python dogrula.py --kok baska/yol    # farklı bir kök klasörde çalışır

VS Code'da Run (▷) düğmesine basmak yeterlidir: api/v1'i kendi konumundan
bulur ve her şeyi (doğrulama + checksum + surumler/ arşivi + katalog.json) yapar.

Beklenen klasör yapısı:
    KOK/ham/<servis>.json            KOK/ham/surumler/<servis>/<surum>.json
    KOK/konsolide/<servis>.json      KOK/konsolide/surumler/<servis>/<surum>.json
    KOK/meta/schema/pdaas-meta-<schema_surumu>.json
    KOK/meta/schema/pdaas-katalog-1.0.0.json
    KOK/meta/kurumlar.json           (isteğe bağlı; kurum kodlarını denetlemek için)
    KOK/katalog.json                 (hazırlama sırasında üretilir)

Çıkış kodu: hata varsa 1, yoksa 0. Uyarılar çıkış kodunu etkilemez.
Gereksinim: pip install jsonschema
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from importlib import import_module

try:
    Draft202012Validator = import_module("jsonschema").Draft202012Validator
except ModuleNotFoundError:
    Draft202012Validator = None


# ─── YENİ: yayın sürümü (tek yerden yönetim) ────────────────────
#   None  → her JSON'un kendi meta.surum.surum alanı kullanılır
#   "..." → tüm servisler bu sürümle yayınlanır; dosyadaki alan ezilir
# Servis bazlı kontrol için sözlük de kullanabilirsiniz:
#   YAYIN_SURUMU = {"nace-kodlari": "2026.04.01", "cpc-kodlari": "2026.04.01"}
YAYIN_SURUMU = None
# ────────────────────────────────────────────────────────────────


KATMANLAR = ("ham", "konsolide")
KATALOG_SEMA = "pdaas-katalog-1.0.0.json"
KOD_RE = re.compile(r"^[0-9A-Z]+(\.[0-9A-Z]+)*$")  # NACE kodları noktalı olabilir (01.11)
PREFIX_RE = re.compile(r"^\d{2,12}$")
GTIP_RE = re.compile(r"^\d{4,12}$")
RENKLER = {
    "slate", "gray", "zinc", "neutral", "stone", "red", "orange", "amber", "yellow",
    "lime", "green", "emerald", "teal", "cyan", "sky", "blue", "indigo", "violet",
    "purple", "fuchsia", "pink", "rose",
}


class Rapor:
    def __init__(self):
        self.hatalar = []
        self.uyarilar = []

    def hata(self, dosya, mesaj):
        self.hatalar.append((dosya, mesaj))

    def uyari(self, dosya, mesaj):
        self.uyarilar.append((dosya, mesaj))

    def yazdir(self):
        for etiket, liste in (("HATA", self.hatalar), ("UYARI", self.uyarilar)):
            for dosya, mesaj in liste:
                print(f"[{etiket}] {dosya}: {mesaj}")
        print(f"\nToplam: {len(self.hatalar)} hata, {len(self.uyarilar)} uyarı")


def ozet(veri):
    """Kanonik JSON (sıralı anahtar, boşluksuz, UTF-8) üzerinden sha256."""
    b = json.dumps(veri, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def yukle(yol, rapor, ad):
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        rapor.hata(ad, "dosya bulunamadı")
    except json.JSONDecodeError as e:
        rapor.hata(ad, f"geçersiz JSON (satır {e.lineno}, sütun {e.colno}): {e.msg}")
    return None


def yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")


def sema_yukle(kok, ad, onbellek, rapor):
    if ad in onbellek:
        return onbellek[ad]
    yol = kok / "meta" / "schema" / ad
    veri = yukle(yol, rapor, f"meta/schema/{ad}")
    onbellek[ad] = Draft202012Validator(veri) if veri else None
    return onbellek[ad]


# ---------------------------------------------------------------- ağaç / harita

def kontrol_agac(doc, ad, rapor):
    kayitlar = doc.get("kayitlar")
    if not isinstance(kayitlar, list) or not kayitlar:
        rapor.hata(ad, "'kayitlar' dolu bir liste olmalı")
        return
    by_kod = {}
    for i, k in enumerate(kayitlar):
        kod = k.get("kod")
        if not isinstance(kod, str) or not KOD_RE.match(kod):
            rapor.hata(ad, f"kayıt #{i}: 'kod' büyük harf/rakamdan oluşan string olmalı ({kod!r})")
            continue
        if kod in by_kod:
            rapor.hata(ad, f"yinelenen kod: {kod}")
            continue
        by_kod[kod] = k
    atlayan = []
    for kod, k in by_kod.items():
        ust, sev = k.get("ust_kod"), k.get("seviye")
        if ust is None:
            if sev != 1:
                rapor.hata(ad, f"{kod}: ust_kod boş ama seviye {sev} (kök kayıt seviye 1 olmalı)")
            continue
        ata = by_kod.get(ust)
        if ata is None:
            rapor.hata(ad, f"{kod}: ust_kod '{ust}' dosyada yok")
            continue
        ust_sev = ata.get("seviye", 0)
        if not isinstance(sev, int) or sev <= ust_sev:
            rapor.hata(ad, f"{kod}: seviye {sev}, üst kayıt '{ust}' seviye {ust_sev}; alt kaydın seviyesi üstünkinden büyük olmalı")
        elif sev > ust_sev + 1:
            atlayan.append(kod)
        if ust_sev >= 2 and not kod.startswith(ust):
            rapor.hata(ad, f"{kod}: kod, üst kodu '{ust}' ile başlamıyor")
    if atlayan:
        rapor.uyari(ad, f"{len(atlayan)} kayıtta seviye atlıyor (arada ara seviye kaydı yok), örn: {', '.join(atlayan[:5])}")


def kontrol_liste(doc, ad, rapor):
    """Düz kod listesi (ör. SGK belge türleri): kod (string, benzersiz) + ad_tr zorunlu, ad_en isteğe bağlı."""
    kayitlar = doc.get("kayitlar")
    if not isinstance(kayitlar, list) or not kayitlar:
        rapor.hata(ad, "'kayitlar' dolu bir liste olmalı")
        return
    gorulen, eksik_en = set(), 0
    for i, k in enumerate(kayitlar):
        kod = k.get("kod")
        if not isinstance(kod, str) or not kod or kod != kod.strip():
            rapor.hata(ad, f"kayıt #{i}: 'kod' boşluksuz, boş olmayan bir string olmalı (sayı değil, tırnak içinde yazın): {kod!r}")
        elif kod in gorulen:
            rapor.hata(ad, f"yinelenen kod: {kod}")
        else:
            gorulen.add(kod)
        etiket = kod if isinstance(kod, str) and kod else f"#{i}"
        if not isinstance(k.get("ad_tr"), str) or not k["ad_tr"].strip():
            rapor.hata(ad, f"{etiket}: 'ad_tr' boş olmayan bir string olmalı")
        en = k.get("ad_en")
        if en is None or en == "":
            eksik_en += 1
        elif not isinstance(en, str):
            rapor.hata(ad, f"{etiket}: 'ad_en' string ya da null olmalı")
    if eksik_en:
        rapor.uyari(ad, f"{eksik_en} kaydın 'ad_en' alanı boş")


def prefix_cakisiyor(a, b):
    return a.startswith(b) or b.startswith(a)


def kontrol_harita(doc, meta, ad, rapor):
    gruplar = doc.get("gruplar")
    kurallar = doc.get("kurallar")
    if not isinstance(gruplar, dict) or not gruplar:
        rapor.hata(ad, "'gruplar' dolu bir nesne olmalı")
        gruplar = {}
    if not isinstance(kurallar, list) or not kurallar:
        rapor.hata(ad, "'kurallar' dolu bir liste olmalı")
        return

    for g, tanim in gruplar.items():
        renk = tanim.get("renk")
        if renk not in RENKLER:
            rapor.uyari(ad, f"grup '{g}': bilinmeyen renk {renk!r}")

    kaynak_kodlari = {k.get("kod") for k in meta.get("kaynaklar", [])}
    kurumlar = set(meta["yayinci"].get("kurumlar", []))
    join_alan = meta["yapi"]["join"]["alan"]
    gorulen_kodlar = set()
    prefixler = []

    def benzersiz(kod, nerede):
        if kod in gorulen_kodlar:
            rapor.hata(ad, f"yinelenen kod: {kod} ({nerede})")
        gorulen_kodlar.add(kod)

    for kural in kurallar:
        kk = kural.get("kod", "?")
        benzersiz(kk, "kural")
        if kural.get("grup") not in gruplar:
            rapor.hata(ad, f"{kk}: grup '{kural.get('grup')}' 'gruplar' içinde tanımlı değil")

        liste = kural.get(join_alan)
        if not isinstance(liste, list) or not liste:
            rapor.hata(ad, f"{kk}: join alanı '{join_alan}' dolu bir liste olmalı")
            liste = []
        for p in liste:
            if not isinstance(p, str) or not PREFIX_RE.match(p):
                rapor.hata(ad, f"{kk}: geçersiz prefix {p!r} (2-12 haneli, string olmalı)")
            else:
                prefixler.append((p, kural.get("oncelik"), kk))
        for p in kural.get("haric_prefix", []):
            if not isinstance(p, str) or not PREFIX_RE.match(p):
                rapor.hata(ad, f"{kk}: geçersiz haric_prefix {p!r}")

        for r in kural.get("randiman_kurallari", []):
            rk = r.get("kod", "?")
            benzersiz(rk, "randıman")
            for alan in ("gtip_girdi", "gtip_cikti"):
                v = r.get(alan)
                if not isinstance(v, str) or not GTIP_RE.match(v):
                    rapor.hata(ad, f"{rk}: {alan} 4-12 haneli string olmalı ({v!r})")
            if r.get("gtip_girdi") == r.get("gtip_cikti"):
                rapor.uyari(ad, f"{rk}: gtip_girdi ve gtip_cikti aynı ({r.get('gtip_girdi')}); girdi/çıktı ayrımı belirsiz, daha uzun prefix verin")
            ro, fo = r.get("randiman_orani"), r.get("fire_orani")
            for etiket, v in (("randiman_orani", ro), ("fire_orani", fo)):
                if v is not None and not (isinstance(v, (int, float)) and 0 <= v <= 1):
                    rapor.hata(ad, f"{rk}: {etiket} 0-1 arasında olmalı ({v!r})")
            if isinstance(ro, (int, float)) and isinstance(fo, (int, float)) and abs(ro + fo - 1) > 1e-9:
                rapor.hata(ad, f"{rk}: randiman_orani + fire_orani = {ro + fo:g}, 1 olmalı")
            if r.get("kaynak_kod") not in kaynak_kodlari:
                rapor.hata(ad, f"{rk}: kaynak_kod {r.get('kaynak_kod')!r} meta.kaynaklar içinde yok")
            girdi = r.get("gtip_girdi")
            if isinstance(girdi, str) and liste and not any(girdi.startswith(p) for p in liste):
                rapor.uyari(ad, f"{rk}: gtip_girdi {girdi}, kuralın prefixlerinden ({', '.join(liste)}) hiçbirine uymuyor")

        for b in kural.get("belgeler", []):
            bk = b.get("kod", "?")
            benzersiz(bk, "belge")
            if b.get("kurum_kod") not in kurumlar:
                rapor.hata(ad, f"{bk}: kurum_kod {b.get('kurum_kod')!r} meta.yayinci.kurumlar içinde yok")

    for i, (p1, o1, k1) in enumerate(prefixler):
        for p2, o2, k2 in prefixler[i + 1:]:
            if k1 != k2 and o1 == o2 and prefix_cakisiyor(p1, p2):
                rapor.uyari(ad, f"{k1} ({p1}) ile {k2} ({p2}) prefixleri çakışıyor ve öncelikleri aynı ({o1}); sonuç belirsiz")


# ---------------------------------------------------------------- checksum / sürüm / bağlar

def kapsam_verisi(doc, meta, ad, rapor):
    kapsam = meta["checksum"]["kapsam"]
    if kapsam not in doc:
        rapor.hata(ad, f"checksum.kapsam '{kapsam}' dosyada yok")
        return None
    return doc[kapsam]


def kontrol_checksum(doc, meta, ad, rapor):
    veri = kapsam_verisi(doc, meta, ad, rapor)
    if veri is None:
        return None
    h = ozet(veri)
    deger = meta["checksum"]["deger"]
    if deger is None:
        rapor.uyari(ad, "checksum.deger boş (hazırlama ile üretilecek)")
    elif deger != h:
        rapor.hata(ad, f"checksum uyuşmuyor (dosyada {deger[:12]}…, hesaplanan {h[:12]}…)")
    return h


def surum_yolu(kok, katman, servis, surum):
    return kok / katman / "surumler" / servis / f"{surum}.json"


def kontrol_surumler(kok, katman, doc, meta, ad, h, rapor):
    servis, surum = meta["servis"]["kod"], meta["surum"]["surum"]
    yol = surum_yolu(kok, katman, servis, surum)
    if not yol.exists():
        rapor.uyari(ad, f"sürüm kopyası yok: {yol.relative_to(kok)} (hazırlama üretir)")
        return
    eski = yukle(yol, rapor, str(yol.relative_to(kok)))
    if eski is None:
        return
    eski_veri = kapsam_verisi(eski, eski["meta"], str(yol.relative_to(kok)), rapor)
    if eski_veri is not None and h is not None and ozet(eski_veri) != h:
        rapor.hata(ad, f"sürüm {surum} zaten yayınlanmış ama içerik farklı; sürüm numarasını artırın (yayınlanan sürümler değişmez)")


def kontrol_konsolide(kok, doc, meta, ad, rapor):
    uretim = meta.get("uretim")
    if not isinstance(uretim, dict):
        return
    kodlar = []
    for hk in uretim["ham_kaynaklar"]:
        sk, sv = hk["servis_kod"], hk["surum"]
        kodlar.append(sk)
        adaylar = [surum_yolu(kok, "ham", sk, sv), kok / "ham" / f"{sk}.json"]
        bulundu = False
        for yol in adaylar:
            if not yol.exists():
                continue
            ham = yukle(yol, rapor, str(yol.relative_to(kok)))
            if not ham or ham.get("meta", {}).get("surum", {}).get("surum") != sv:
                continue
            bulundu = True
            veri = ham.get(ham["meta"]["checksum"]["kapsam"])
            if veri is not None and ozet(veri) != hk["checksum"]:
                rapor.hata(ad, f"uretim.ham_kaynaklar: {sk} {sv} checksum'ı ham dosyayla uyuşmuyor")
            break
        if not bulundu:
            rapor.hata(ad, f"uretim.ham_kaynaklar: ham/{sk} sürüm {sv} bulunamadı")
        else:
            son = kok / "ham" / f"{sk}.json"
            if son.exists():
                try:
                    with open(son, encoding="utf-8") as f:
                        son_surum = json.load(f)["meta"]["surum"]["surum"]
                except (KeyError, json.JSONDecodeError):
                    son_surum = None
                if son_surum and son_surum != sv:
                    rapor.uyari(ad, f"konsolide, ham/{sk} sürüm {sv} ile üretilmiş; ham'ın son sürümü {son_surum} (konsolide bayat)")
    stem = meta["servis"]["kod"]
    if len(kodlar) == 1 and stem != kodlar[0]:
        rapor.uyari(ad, f"tek ham kaynaktan ({kodlar[0]}) üretilmiş ama servis kodu farklı ({stem}); aynı adı kullanın")
    if len(kodlar) > 1 and stem in kodlar:
        rapor.uyari(ad, f"birden çok ham kaynağı birleştiriyor ama ham dosyalardan birinin adını taşıyor ({stem}); yeni bir ad verin")


def kontrol_kurumlar(kok, kullanilan, rapor):
    yol = kok / "meta" / "kurumlar.json"
    if not yol.exists():
        rapor.uyari("meta/kurumlar.json", "dosya yok; kurum kodları denetlenemedi")
        return
    veri = yukle(yol, rapor, "meta/kurumlar.json")
    if veri is None:
        return
    if isinstance(veri, dict) and "kurumlar" in veri:
        veri = veri["kurumlar"]
    kodlar = set(veri.keys()) if isinstance(veri, dict) else {k.get("kod") for k in veri if isinstance(k, dict)}
    for kod, dosyalar in sorted(kullanilan.items()):
        if kod not in kodlar:
            rapor.uyari("meta/kurumlar.json", f"kurum kodu '{kod}' tanımlı değil (kullanan: {', '.join(sorted(dosyalar))})")


# ---------------------------------------------------------------- katalog

def katalog_uret(bilgiler, url_on_ek):
    servisler = {}
    for b in bilgiler:
        m = b["meta"]
        s = servisler.setdefault(m["servis"]["kod"], {
            "kod": m["servis"]["kod"],
            "ad": m["servis"]["ad"],
            "tip": m["yapi"]["tip"],
            "kod_sistemi": m["yapi"]["kod_sistemi"],
            "katmanlar": {},
        })
        kod = m["servis"]["kod"]
        s["katmanlar"][m["katman"]] = {
            "son": m["surum"]["surum"],
            "url": f"{url_on_ek}/{m['katman']}/{kod}.json",
            "surumler_url": f"{url_on_ek}/{m['katman']}/surumler/{kod}/",
            "checksum": b["hash"],
        }
    return {
        "schema_surumu": "1.0.0",
        "guncelleme": max(b["meta"]["surum"]["guncelleme"] for b in bilgiler),
        "servisler": sorted(servisler.values(), key=lambda s: s["kod"]),
    }


def kontrol_katalog(kok, bilgiler, onbellek, rapor):
    yol = kok / "katalog.json"
    if not yol.exists():
        rapor.uyari("katalog.json", "dosya yok (hazırlama üretir)")
        return
    kat = yukle(yol, rapor, "katalog.json")
    if kat is None:
        return
    sema = sema_yukle(kok, KATALOG_SEMA, onbellek, rapor)
    if sema:
        for e in sema.iter_errors(kat):
            rapor.hata("katalog.json", f"{'.'.join(map(str, e.absolute_path)) or '(kök)'}: {e.message}")
    kayitli = {(s["kod"], k): v for s in kat.get("servisler", []) for k, v in s.get("katmanlar", {}).items()}
    for b in bilgiler:
        m = b["meta"]
        anahtar = (m["servis"]["kod"], m["katman"])
        v = kayitli.pop(anahtar, None)
        if v is None:
            rapor.hata("katalog.json", f"{anahtar[1]}/{anahtar[0]} katalogda yok")
        elif v.get("son") != m["surum"]["surum"] or v.get("checksum") != b["hash"]:
            rapor.hata("katalog.json", f"{anahtar[1]}/{anahtar[0]} katalogdaki sürüm/checksum dosyayla uyuşmuyor")
    for (servis, katman) in kayitli:
        rapor.hata("katalog.json", f"{katman}/{servis} katalogda var ama dosyası yok")


# ---------------------------------------------------------------- ana akış

def surum_uygula(meta, ad, rapor):
    """YAYIN_SURUMU doluysa meta.surum.surum'u onunla değiştirir (servis bazlı sözlük desteklenir)."""
    if not YAYIN_SURUMU:
        return
    servis_kod = meta.get("servis", {}).get("kod")
    if isinstance(YAYIN_SURUMU, dict):
        yeni = YAYIN_SURUMU.get(servis_kod)
    else:
        yeni = YAYIN_SURUMU
    if not yeni:
        return
    mevcut = meta.get("surum", {}).get("surum")
    if mevcut and mevcut != yeni:
        rapor.uyari(ad, f"dosyadaki sürüm ({mevcut}) ile YAYIN_SURUMU ({yeni}) farklı; {yeni} yazılacak")
    meta.setdefault("surum", {})["surum"] = yeni


def isle(yol, katman, kok, rapor, onbellek):
    ad = f"{katman}/{yol.name}"
    doc = yukle(yol, rapor, ad)
    if doc is None:
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict):
        rapor.hata(ad, "kökte 'meta' nesnesi yok")
        return None
    meta = doc["meta"]

    # ─── YENİ: global sürüm sabiti uygula ───
    surum_uygula(meta, ad, rapor)
    # ────────────────────────────────────────

    sv = meta.get("schema_surumu")
    sema = sema_yukle(kok, f"pdaas-meta-{sv}.json", onbellek, rapor)
    if sema is None:
        return None
    hatalar = sorted(sema.iter_errors(meta), key=lambda e: list(map(str, e.absolute_path)))
    for e in hatalar:
        rapor.hata(ad, f"meta.{'.'.join(map(str, e.absolute_path)) or '(kök)'}: {e.message}")
    if hatalar:
        return None

    if meta["katman"] != katman:
        rapor.hata(ad, f"meta.katman '{meta['katman']}' ama dosya '{katman}/' klasöründe")
    if meta["servis"]["kod"] != yol.stem:
        rapor.hata(ad, f"meta.servis.kod '{meta['servis']['kod']}' dosya adıyla ({yol.stem}) aynı olmalı")

    tip = meta["yapi"]["tip"]
    if tip == "agac":
        kontrol_agac(doc, ad, rapor)
    elif tip == "liste":
        kontrol_liste(doc, ad, rapor)
    else:
        kontrol_harita(doc, meta, ad, rapor)

    h = kontrol_checksum(doc, meta, ad, rapor)
    kontrol_surumler(kok, katman, doc, meta, ad, h, rapor)
    if katman == "konsolide":
        kontrol_konsolide(kok, doc, meta, ad, rapor)
    return {"yol": yol, "katman": katman, "doc": doc, "meta": meta, "hash": h, "ad": ad}


def varsayilan_kok():
    """dogrula.py'nin bulunduğu klasörün altındaki api/v1."""
    return Path(__file__).resolve().parent / "api" / "v1"


def main():
    if Draft202012Validator is None:
        print("Gereksinim eksik: pip install jsonschema", file=sys.stderr)
        return 1

    ap = argparse.ArgumentParser(description="PDaaS yayın klasörü doğrulama + hazırlama")
    ap.add_argument("--kok", default=None, help="kök klasör (varsayılan: dogrula.py'nin yanındaki api/v1)")
    # ─── YENİ: --hazirla artık VARSAYILAN; --sadece-dogrula ile kapatılır ───
    ap.add_argument("--hazirla", dest="hazirla", action="store_true", default=True,
                    help="(varsayılan) checksum, surumler/ kopyası ve katalog.json üret")
    ap.add_argument("--sadece-dogrula", dest="hazirla", action="store_false",
                    help="hiçbir dosya yazma; yalnızca denetle")
    # ────────────────────────────────────────────────────────────────────────
    ap.add_argument("--url-on-ek", default="/api/v1")
    args = ap.parse_args()

    kok = Path(args.kok).expanduser().resolve() if args.kok else varsayilan_kok()
    print(f"Kök klasör: {kok}")
    if not kok.is_dir():
        print(f"HATA: kök klasör yok: {kok}", file=sys.stderr)
        return 1

    rapor = Rapor()
    onbellek = {}
    bilgiler = []
    for katman in KATMANLAR:
        klasor = kok / katman
        if not klasor.is_dir():
            continue
        for yol in sorted(klasor.glob("*.json")):
            b = isle(yol, katman, kok, rapor, onbellek)
            if b:
                bilgiler.append(b)

    kullanilan = {}
    for b in bilgiler:
        for kod in b["meta"]["yayinci"]["kurumlar"]:
            kullanilan.setdefault(kod, set()).add(b["ad"])
    if bilgiler:
        kontrol_kurumlar(kok, kullanilan, rapor)

    if not args.hazirla and bilgiler:
        kontrol_katalog(kok, bilgiler, onbellek, rapor)

    if args.hazirla:
        # checksum ve katalog eksikliği hazırlama öncesinde hata sayılmaz
        engel = [h for h in rapor.hatalar if "checksum" not in h[1] or "uyuşmuyor" not in h[1]]
        if engel or not bilgiler:
            rapor.yazdir()
            print("\nHazırlama yapılmadı: önce yukarıdaki hataları giderin.")
            return 1
        for b in bilgiler:
            b["meta"]["checksum"]["deger"] = b["hash"]
            yaz(b["yol"], b["doc"])
            yaz(surum_yolu(kok, b["katman"], b["meta"]["servis"]["kod"], b["meta"]["surum"]["surum"]), b["doc"])
        yaz(kok / "katalog.json", katalog_uret(bilgiler, args.url_on_ek))
        print(f"\n{len(bilgiler)} dosya hazırlandı; checksum, surumler/ ve katalog.json yazıldı.\n")
        rapor2 = Rapor()
        return main_dogrulama_ozeti(kok, rapor2)

    rapor.yazdir()
    return 1 if rapor.hatalar else 0


def main_dogrulama_ozeti(kok, rapor):
    """Hazırlama sonrası aynı klasörü yeniden denetle."""
    onbellek, bilgiler = {}, []
    for katman in KATMANLAR:
        klasor = kok / katman
        if klasor.is_dir():
            for yol in sorted(klasor.glob("*.json")):
                b = isle(yol, katman, kok, rapor, onbellek)
                if b:
                    bilgiler.append(b)
    kullanilan = {}
    for b in bilgiler:
        for kod in b["meta"]["yayinci"]["kurumlar"]:
            kullanilan.setdefault(kod, set()).add(b["ad"])
    if bilgiler:
        kontrol_kurumlar(kok, kullanilan, rapor)
    kontrol_katalog(kok, bilgiler, onbellek, rapor)
    rapor.yazdir()
    return 1 if rapor.hatalar else 0


if __name__ == "__main__":
    sys.exit(main())