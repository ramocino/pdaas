/* PDaaS ortak veri katmanı
 * - IndexedDB önbelleği (stale-while-revalidate): ikinci ziyarette veri ANINDA gelir
 * - Yedek URL'leri sırayla değil PARALEL dener (404'ler artık süre eklemez)
 * - Çalışan URL'yi hatırlar (bir sonraki sefer tek istek)
 * - Akış (stream) okuma ile gerçek ilerleme bilgisi verir
 * - Süre ölçümü (PDaaS.log) geliştiriciler için
 */
(function (g) {
  'use strict';
  const DB = 'pdaas-cache-v1', ST = 'kv', FRESH = 6 * 3600e3; // 6 saat taze sayılır
  const log = [];

  function idb() {
    return new Promise((res, rej) => {
      const r = indexedDB.open(DB, 1);
      r.onupgradeneeded = () => r.result.createObjectStore(ST);
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
  }
  async function dbGet(k) {
    try {
      const d = await idb();
      return await new Promise(res => {
        const q = d.transaction(ST).objectStore(ST).get(k);
        q.onsuccess = () => res(q.result || null);
        q.onerror = () => res(null);
      });
    } catch (_) { return null; }
  }
  async function dbPut(k, v) {
    try { const d = await idb(); d.transaction(ST, 'readwrite').objectStore(ST).put(v, k); } catch (_) {}
  }
  async function dbClear() {
    try { const d = await idb(); d.transaction(ST, 'readwrite').objectStore(ST).clear(); } catch (_) {}
  }

  async function netFetch(url, { signal, onProgress } = {}) {
    const r = await fetch(url, { headers: { Accept: 'application/json' }, signal });
    if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
    const etag = r.headers.get('ETag') || '';
    const total = +r.headers.get('Content-Length') || 0;
    let text;
    if (r.body && onProgress) {
      const rd = r.body.getReader(), parts = [];
      let got = 0;
      for (;;) {
        const { done, value } = await rd.read();
        if (done) break;
        parts.push(value); got += value.length;
        onProgress(got, total);
      }
      const buf = new Uint8Array(got); let o = 0;
      for (const p of parts) { buf.set(p, o); o += p.length; }
      text = new TextDecoder().decode(buf);
    } else {
      text = await r.text();
    }
    return { data: JSON.parse(text), etag, url, bytes: text.length, status: r.status };
  }

  // Yedek URL'leri paralel yarıştır; ilk başaran kazanır, diğerleri iptal edilir
  function race(urls, opts) {
    if (urls.length === 1) return netFetch(urls[0], opts);
    const ctrls = urls.map(() => new AbortController());
    return Promise.any(urls.map((u, i) =>
      netFetch(u, { ...opts, signal: ctrls[i].signal }).then(r => {
        ctrls.forEach((c, j) => { if (j !== i) c.abort(); });
        return r;
      })
    ));
  }

  async function fromNetwork(name, urls, opts) {
    const hint = localStorage.getItem('pdaas_ep:' + name);
    const first = hint && urls.includes(hint) ? [hint] : urls;
    let r;
    try { r = await race(first, opts); }
    catch (e) {
      if (first.length === urls.length) throw new Error(name + ': hiçbir uç nokta yanıt vermedi (' + urls.join(' | ') + ')');
      r = await race(urls, opts).catch(() => { throw new Error(name + ': hiçbir uç nokta yanıt vermedi (' + urls.join(' | ') + ')'); });
    }
    try { localStorage.setItem('pdaas_ep:' + name, r.url); } catch (_) {}
    return r;
  }

  /**
   * load(ad, [url1, url2…], { onProgress(got,total), onUpdate(data) })
   * → { data, from:'cache'|'network', ms, url, bytes }
   */
  async function load(name, urls, opt = {}) {
    const t0 = performance.now(), key = 'd:' + name;
    const cached = await dbGet(key);

    if (cached && cached.data) {
      const age = Date.now() - cached.t;
      if (age > FRESH) {
        // Arka planda yenile; kullanıcı beklemez
        fromNetwork(name, urls, {}).then(r => {
          const degisti = r.etag ? r.etag !== cached.etag : r.bytes !== cached.bytes;
          dbPut(key, { data: r.data, etag: r.etag, bytes: r.bytes, t: Date.now(), url: r.url });
          if (degisti && opt.onUpdate) opt.onUpdate(r.data);
        }).catch(() => {});
      }
      const ms = Math.round(performance.now() - t0);
      log.push({ name, from: 'cache', ms, bytes: cached.bytes, url: cached.url });
      return { data: cached.data, from: 'cache', ms, url: cached.url, bytes: cached.bytes };
    }

    const r = await fromNetwork(name, urls, { onProgress: opt.onProgress });
    dbPut(key, { data: r.data, etag: r.etag, bytes: r.bytes, t: Date.now(), url: r.url });
    const ms = Math.round(performance.now() - t0);
    log.push({ name, from: 'network', ms, bytes: r.bytes, url: r.url });
    return { data: r.data, from: 'network', ms, url: r.url, bytes: r.bytes };
  }

  g.PDaaS = { load, log, clear: dbClear };
})(window);