#!/usr/bin/env python3
"""GitHub Actions で実行：国土交通省・水資源機構の公式ページに載っているダムカードの画像を集める。

- 対象は各ダムページにリンクしている mlit.go.jp / water.go.jp のページと、その事務所のトップページ、
  そこから「ダムカード」と書かれたリンクで1段たどったページだけ
- 画像のファイル名か alt に card / カード が入っていて、カードの縦横比（88:63 前後）のものだけ使う
- 「転載」「無断」「複製を禁」などの断り書きがあるページの画像は使わない（PDL1.0 の対象外のため）
- 画像は assets/cards/<slug>-<n>.jpg に保存し、出典ページを tools/photos/cards_official.tsv に書き出す
"""
import glob, hashlib, html, io, os, re, time, urllib.parse, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "dam-com-card-bot/1.0 (https://xn--6ck4c.com/)"}
HOST_OK = re.compile(r"(^|\.)(mlit\.go\.jp|water\.go\.jp)$")
BAN = re.compile(r"転載|無断|複製を禁|使用を禁|二次利用を禁|利用を禁")
OUT_DIR = os.path.join(ROOT, "assets", "cards")
EXTRA = {"dam-card": ["https://www.mlit.go.jp/river/kankyo/campaign/shunnkan/damcard.html"]}

def get(url, binary=False):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            data = r.read(3_000_000)
            if binary:
                return data
            ct = r.headers.get_content_charset()
            for enc in [ct, "utf-8", "shift_jis", "euc-jp"]:
                if not enc:
                    continue
                try:
                    return data.decode(enc)
                except Exception:
                    pass
            return data.decode("utf-8", "replace")
    except Exception as e:
        print("  fail", url, e)
        return None

def ok_host(u):
    h = urllib.parse.urlparse(u).hostname or ""
    return bool(HOST_OK.search(h)) and u.startswith("https://")

def title_of(s):
    m = re.search(r"<title[^>]*>(.*?)</title>", s, re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()[:80] if m else ""

def pages_for(slug, path, seeds=()):
    s = open(path, encoding="utf-8").read()
    urls = [u for u in re.findall(r'href="(https://[^"#]+)"', s) if ok_host(u) and not u.lower().endswith((".pdf", ".xlsx", ".xls", ".zip"))]
    tops = set()
    for u in urls:
        p = urllib.parse.urlparse(u)
        seg = [x for x in p.path.split("/") if x]
        if seg and "." not in seg[0] and "mlit.go.jp" in p.hostname and p.hostname != "www.mlit.go.jp":
            tops.add(f"https://{p.hostname}/{seg[0]}/")
    # 全国共通のページ（www.mlit.go.jp/river/... のカード一覧など）は、そのダムの画像とは限らないので除く
    urls = [u for u in urls if urllib.parse.urlparse(u).hostname != "www.mlit.go.jp"]
    return list(dict.fromkeys(list(seeds) + urls + sorted(tops) + EXTRA.get(slug, [])))[:14]

REGION_PAGES = [f"https://www.mlit.go.jp/river/kankyo/campaign/shunnkan/damcard{n}.html" for n in range(81, 91)]

def region_seeds(names):
    """国土交通省のダムカード案内（地方別）から、ダム名ごとの「ホームページURL」を拾う。"""
    seeds = {}
    for rp in REGION_PAGES:
        s = get(rp)
        time.sleep(0.5)
        if not s:
            continue
        for slug, name in names.items():
            for m in re.finditer(re.escape(name), s):
                chunk = s[m.end():m.end() + 5000]
                nxt = re.search(r"ダムカード配布場所", chunk)
                for u in re.findall(r'href="(https?://[^"#]+)"', chunk):
                    u = u.replace("http://", "https://", 1)
                    if ok_host(u) and "/river/kankyo/" not in u and not u.lower().endswith((".pdf", ".xlsx")):
                        seeds.setdefault(slug, [])
                        if u not in seeds[slug]:
                            seeds[slug].append(u)
                        break
                if nxt is None:
                    continue
    return seeds

def card_images(page_url, s):
    out = []
    for m in re.finditer(r"<img\b[^>]*>", s, re.I):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag) or re.search(r"src='([^']+)'", tag)
        if not src:
            continue
        alt = re.search(r'alt="([^"]*)"', tag)
        alt = html.unescape(alt.group(1)) if alt else ""
        u = urllib.parse.urljoin(page_url, html.unescape(src.group(1)))
        if not ok_host(u) or not re.search(r"\.(jpe?g|png|gif)$", u, re.I):
            continue
        if re.search(r"card|カード", u + " " + alt, re.I) and not re.search(r"bnr|banner|icon|btn|logo", u, re.I):
            out.append((u, alt))
    return out

def follow_links(page_url, s):
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', s, re.I | re.S):
        text = re.sub(r"<[^>]+>", "", m.group(2))
        u = urllib.parse.urljoin(page_url, html.unescape(m.group(1)))
        if ok_host(u) and ("ダムカード" in text or re.search(r"dam.?card", u, re.I)) and not u.lower().endswith((".pdf", ".xlsx", ".xls")):
            out.append(u)
    return out[:3]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    targets = [(os.path.basename(os.path.dirname(p)), p) for p in sorted(glob.glob(os.path.join(ROOT, "dam", "*", "index.html")))]
    targets += [("kurobe", os.path.join(ROOT, "kurobe", "index.html")), ("dam-card", os.path.join(ROOT, "dam-card", "index.html"))]
    names = {}
    for slug, path in targets:
        m = re.search(r"<h1>(.+?ダム)", open(path, encoding="utf-8").read())
        if m and slug != "dam-card":
            names[slug] = m.group(1)
    seeds = region_seeds(names)
    tsv = os.path.join(ROOT, "tools", "photos", "cards_official.tsv")
    rows = open(tsv, encoding="utf-8").read().splitlines() if os.path.exists(tsv) else ["slug\timage\tsource_page\tsource_title\talt"]
    have = {r.split("\t")[1] for r in rows[1:] if "\t" in r}
    for slug, path in targets:
        seen_pages, seen_img, saved = set(), set(), 0
        queue = pages_for(slug, path, seeds.get(slug, []))
        print(slug, names.get(slug, ""), len(queue), "pages", "seed:" + ",".join(seeds.get(slug, [])))
        while queue and saved < 4 and len(seen_pages) < 20:
            u = queue.pop(0)
            if u in seen_pages:
                continue
            seen_pages.add(u)
            s = get(u)
            time.sleep(0.4)
            if not s:
                continue
            if BAN.search(re.sub(r"<[^>]+>", "", s)):
                print("  skip (restriction text)", u)
                continue
            queue += [x for x in follow_links(u, s) if x not in seen_pages]
            for img, alt in card_images(u, s):
                if img in seen_img or saved >= 4:
                    continue
                seen_img.add(img)
                name = f"{slug}-{hashlib.md5(img.encode()).hexdigest()[:8]}.jpg"
                if "/assets/cards/" + name in have:
                    saved += 1
                    continue
                data = get(img, binary=True)
                time.sleep(0.3)
                if not data or len(data) < 4000:
                    continue
                try:
                    im = Image.open(io.BytesIO(data)).convert("RGB")
                except Exception:
                    continue
                w, h = im.size
                r = w / h
                if min(w, h) < 150 or not (1.25 <= r <= 1.55 or 0.64 <= r <= 0.8):
                    continue
                im.thumbnail((640, 640))
                saved += 1
                im.save(os.path.join(OUT_DIR, name), "JPEG", quality=85)
                have.add("/assets/cards/" + name)
                rows.append("\t".join([slug, "/assets/cards/" + name, u, title_of(s).replace("\t", " "), alt.replace("\t", " ")]))
                print("  ok", img, alt)
    open(tsv, "w", encoding="utf-8").write("\n".join(rows) + "\n")

if __name__ == "__main__":
    main()
