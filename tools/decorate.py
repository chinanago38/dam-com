#!/usr/bin/env python3
"""全ページの見た目を整える後処理（何度実行しても同じ結果になる）。
- 見出し(h2)ごとのまとまりをブロック（カード）表示にする
- ページ上部のタイトル部分を帯（page-hero）にし、ダムのページには高さ・形式・所在地のチップを付ける
- 表を横スクロールできる枠で包む
- ダムのページに「高さくらべ」の図、ランキングページに上位15の棒グラフを入れる
tools/build.py の最後に自動で実行される。
"""
import glob, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_VER = "20261125e"
MARK = "<!--decorated-->"


def strip(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def height_of(main):
    m = re.search(r"<th>堤高</th>\s*<td>(.*?)</td>", main, re.S)
    if not m:
        return None, None
    txt = strip(m.group(1))
    n = re.search(r"([0-9]{2,3}(?:\.[0-9])?)\s*m", txt)
    return (float(n.group(1)) if n else None), txt


def cell(main, label):
    m = re.search(r"<th>" + label + r"</th>\s*<td>(.*?)</td>", main, re.S)
    return strip(m.group(1)) if m else None


def bars(items, caption):
    mx = max(v for _, v, _ in items)
    rows = []
    for name, v, me in items:
        w = max(8, round(v / mx * 100))
        rows.append(f'<div class="bar{" me" if me else ""}"><span class="name">{html.escape(name)}</span>'
                    f'<span class="track"><span class="fill" style="width:{w}%">{v:g}m</span></span></div>')
    return f'<figure class="figure"><div class="bars">{"".join(rows)}</div><figcaption>{html.escape(caption)}</figcaption></figure>'


def wrap_tables(s):
    return re.sub(r"(?<!<div class=\"table-wrap\">)(<table\b.*?</table>)", r'<div class="table-wrap">\1</div>', s, flags=re.S)


def blockify(body):
    """body = main の中身（crumb と hero を除いた部分）を h2 ごとのブロックに分ける"""
    tail = ""
    k = body.find('<section class="sources">')
    if k >= 0:
        tail = body[k:].replace('<section class="sources">', '<section class="sources block">', 1)
        body = body[:k]
    parts = re.split(r"(?=<h2[ >])", body)
    out = []
    for p in parts:
        if not p.strip():
            continue
        if p.lstrip().startswith("<h2"):
            out.append(f'<section class="block">{p.rstrip()}</section>\n')
        elif strip(p):
            out.append(f'<div class="block lead-block">{p.strip()}</div>\n')
    return "".join(out) + tail


def load_photos():
    photos = {}
    d = os.path.join(ROOT, "tools", "photos")
    if os.path.isdir(d):
        for f in sorted(glob.glob(os.path.join(d, "*.tsv"))):
            for line in open(f, encoding="utf-8").read().splitlines()[1:]:
                c = line.split("\t")
                if len(c) < 7 or not re.match(r"https://(upload|thumb)\.wikimedia\.org/", c[1]):
                    continue
                c[1] = c[1].split("?")[0]
                a = c[3]
                a = re.sub(r"^No machine-readable author provided\.\s*(.+?) assumed.*$", r"\1", a)
                a = re.sub(r"^photo:\s*", "", a)
                a = re.sub(r"\s*\(talk\).*$", "", a)
                a = re.sub(r",?\s*(Taken with|with) .*$", "", a).strip()
                if not a or a == "不明":
                    if "public domain" not in c[4].lower() and "cc0" not in c[4].lower():
                        continue  # 表示が必要なライセンスで作者がわからない写真は使わない
                    a = "作者不明"
                c[3] = a
                photos[c[0].strip()] = c
    ov = os.path.join(d, "alt_overrides.tsv")
    if os.path.exists(ov):
        for line in open(ov, encoding="utf-8").read().splitlines()[1:]:
            k, _, alt = line.partition("\t")
            if k in photos and alt:
                photos[k][6] = alt
    return photos


def load_cards():
    """tools/photos/cards_approved.tsv に人の目で確認して載せた画像だけ使う。出典は cards_official.tsv から引く。"""
    src = {}
    f = os.path.join(ROOT, "tools", "photos", "cards_official.tsv")
    if os.path.exists(f):
        for line in open(f, encoding="utf-8").read().splitlines()[1:]:
            c = line.split("\t")
            if len(c) >= 4 and re.match(r"https://[^/]*(mlit|water)\.go\.jp/", c[2]):
                src[c[1]] = (c[2], c[3])
    cards = {}
    f = os.path.join(ROOT, "tools", "photos", "cards_approved.tsv")
    if os.path.exists(f):
        for line in open(f, encoding="utf-8").read().splitlines()[1:]:
            c = line.split("\t")
            if len(c) >= 3 and c[1] in src and os.path.exists(os.path.join(ROOT, c[1].lstrip("/"))):
                cards.setdefault(c[0], []).append((c[1], c[2]) + src[c[1]])
    return cards


def add_cards(s, slug, cards):
    """公式ページのダムカード画像を「ダムカード」の見出しの下に入れる（PDL1.0、出典表示つき）。"""
    s = re.sub(r"<!--cards--><figure class=\"cardimg\">.*?</figure>\n?", "", s, flags=re.S)
    if slug not in cards:
        return s
    e = html.escape
    imgs = "".join(f'<img src="{e(img)}?v={CSS_VER}" alt="{e(cap)}" title="{e(cap)}" loading="lazy" decoding="async" width="320">' for img, cap, _, _ in cards[slug])
    caps = "／".join(cap for _, cap, _, _ in cards[slug])
    src = "、".join(dict.fromkeys(f'<a href="{e(u)}" rel="noopener" target="_blank">{e(t or u)}</a>' for _, _, u, t in cards[slug]))
    fig = (f'<!--cards--><figure class="cardimg"><div class="cardimg-row">{imgs}</div>'
           f'<figcaption>{e(caps)}（画像は縮小して掲載）<br>出典：{src}（国土交通省のページ。公共データ利用規約 PDL1.0 にもとづいて掲載）</figcaption></figure>\n')
    m = re.search(r'<section class="block"><h2>[^<]*ダムカード[^<]*</h2>\n?', s) or re.search(r'<section class="block"><h2>[^<]*</h2>\n?', s)
    if not m:
        return s
    return s[:m.end()] + fig + s[m.end():]


def add_photo(s, slug, photos):
    s = re.sub(r"<!--photo--><figure class=\"photo\">.*?</figure>\n", "", s, flags=re.S)
    if slug not in photos:
        return s
    _, url, page, author, lic, lic_url, alt = photos[slug][:7]
    e = html.escape
    lic_html = f'<a href="{e(lic_url)}" rel="noopener license" target="_blank">{e(lic)}</a>' if lic_url.startswith("http") else e(lic)
    fig = (f'<!--photo--><figure class="photo"><img src="{e(url)}" alt="{e(alt)}" loading="lazy" decoding="async">'
           f'<figcaption>{e(alt)}　写真：{e(author)} / {lic_html}（<a href="{e(page)}" rel="noopener" target="_blank">Wikimedia Commons</a>）</figcaption></figure>\n')
    i = s.find('<div class="page-hero">')
    if i < 0:
        return s
    depth, j = 0, -1
    for mm in re.finditer(r"<div\b|</div>", s[i:]):
        depth += 1 if mm.group(0) == "<div" else -1
        if depth == 0:
            j = i + mm.end(); break
    if j > 0 and s[j:j+1] == "\n":
        j += 1
    elif j > 0:
        s = s[:j] + "\n" + s[j:]; j += 1
    return s[:j] + fig + s[j:] if j > 0 else s


CARDS = None


def card_hook(s, rel0):
    global CARDS
    if CARDS is None:
        CARDS = load_cards()
    cslug = "dam-card" if rel0 == "dam-card/index.html" else "kurobe" if rel0 == "kurobe/index.html" else (rel0.split("/")[1] if rel0.startswith("dam/") else None)
    if not cslug:
        return s
    return add_cards(s, cslug, CARDS)


def process(path, dams, photos=None):
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"/assets/style\.css\?v=[0-9a-z]+", f"/assets/style.css?v={CSS_VER}", s)
    rel0 = os.path.relpath(path, ROOT).replace(os.sep, "/")
    slug0 = "kurobe" if rel0 == "kurobe/index.html" else "File:Damcard.jpg" if rel0 == "dam-card/index.html" else (rel0.split("/")[1] if rel0.startswith("dam/") else None)
    if rel0 == "index.html":
        n_dam = len(glob.glob(os.path.join(ROOT, "dam", "*", "index.html"))) + 1
        s = re.sub(r'<(div|a) class="stat"( href="[^"]*")?><b>[0-9]+</b><small>ダムの見学ガイド</small>', f'<a class="stat" href="/ranking/"><b>{n_dam}</b><small>ダムの見学ガイド</small>', s)
        if photos and "naruko" in photos:
            s = re.sub(r"<!--photo--><figure class=\"photo\">.*?</figure>\n", "", s, flags=re.S)
            _, url, page, author, lic, lic_url, alt = photos["naruko"][:7]
            e = html.escape
            fig = (f'<!--photo--><figure class="photo"><img src="{e(url)}" alt="{e(alt)}" loading="lazy" decoding="async">'
                   f'<figcaption>{e(alt)}（宮城県）　写真：{e(author)} / <a href="{e(lic_url)}" rel="noopener license" target="_blank">{e(lic)}</a>'
                   f'（<a href="{e(page)}" rel="noopener" target="_blank">Wikimedia Commons</a>）</figcaption></figure>\n')
            s = s.replace('<main><div class="wrap">', '<main><div class="wrap">\n' + fig, 1)
    if MARK in s:
        if slug0 and photos:
            s = add_photo(s, slug0, photos)
        s = card_hook(s, rel0)
        open(path, "w", encoding="utf-8").write(s)
        return False
    m = re.search(r"(<main><div class=\"wrap\">)(.*)(</div></main>)", s, re.S)
    if not m:
        return False
    main = m.group(2)
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    is_top = rel == "index.html"

    crumb = ""
    cm = re.search(r"\s*<div class=\"crumb\">.*?</div>", main, re.S)
    if cm:
        crumb, main = cm.group(0), main.replace(cm.group(0), "", 1)

    hero = ""
    if not is_top:
        hm = re.search(r"\s*<h1>(.*?)</h1>\s*(<p class=\"updated\">.*?</p>)?", main, re.S)
        if hm:
            main = main.replace(hm.group(0), "", 1)
            chips = ""
            if rel.startswith("dam/") or rel == "kurobe/index.html":
                h, htxt = height_of(main)
                kinds = []
                if htxt:
                    kinds.append(f"高さ <b>{html.escape(htxt.split('（')[0])}</b>")
                t = cell(main, "形式")
                if t:
                    kinds.append(html.escape(t.split("（")[0]))
                loc = cell(main, "所在地")
                if loc:
                    kinds.append(html.escape(loc.split("（")[0]))
                lake = cell(main, "ダム湖")
                if lake and lake != "—":
                    kinds.append("ダム湖：" + html.escape(lake.split("（")[0]))
                chips = '<div class="chips">' + "".join(f'<span class="chip">{k}</span>' for k in kinds) + "</div>" if kinds else ""
            hero = f'\n  <div class="page-hero"><h1>{hm.group(1)}</h1>{hm.group(2) or ""}{chips}</div>\n'

    # 図：ダムのページの高さくらべ
    if rel.startswith("dam/") or rel == "kurobe/index.html":
        h, _ = height_of(main)
        name = strip(re.search(r"<h1>(.*?)</h1>", s, re.S).group(1)) if re.search(r"<h1>(.*?)</h1>", s, re.S) else ""
        name = re.sub(r"(の見学ガイド|の観光放流.*|・.*|の見学.*|｜.*)$", "", name)
        if h:
            items = []
            if "黒部" not in name:
                items.append(("黒部ダム（日本一）", 186.0, False))
            items.append((name or "このダム", h, True))
            items.append(("高さ50位のダム", 114.0, False))
            items.append(("ダムの基準（15m）", 15.0, False))
            items.sort(key=lambda x: -x[1])
            fig = bars(items, f"{name}の高さを、日本一の黒部ダム、高さ50位のダム（114m）、法律上ダムと呼ばれる最低の高さ（15m）と比べた図です。")
            fig_block = f'<section class="block"><h2>高さくらべ</h2>{fig}</section>\n'
            # 基本情報ブロックの直後に置く
            idx = main.find("<h2>基本情報</h2>")
            nxt = main.find("<h2", idx + 5) if idx >= 0 else -1
            if nxt > 0:
                main = main[:nxt] + "\n  <h2>高さくらべ</h2>" + fig + "\n" + main[nxt:]
            else:
                main = main + fig_block

    # 図：ランキング上位15
    if rel == "ranking/index.html" and dams:
        top = dams[:15]
        fig = bars([(d[0], d[1], False) for d in top], "日本のダムの高さ（堤高）上位15。数字は基礎の岩盤からダムのいちばん上までの高さです。")
        idx = main.find("<table")
        main = main[:idx] + "<h2>上位15をグラフで見る</h2>" + fig + "\n  <h2>上位50の一覧</h2>\n" + main[idx:]

    main = wrap_tables(main)
    main = blockify(main)

    if is_top:
        n_dam = len(glob.glob(os.path.join(ROOT, "dam", "*", "index.html"))) + 1
        s = re.sub(r'(<section class="hero"><div class="wrap">.*?)(</div></section>)',
                   lambda mm: mm.group(1) + f'\n  <div class="stats"><a class="stat" href="/ranking/"><b>{n_dam}</b><small>ダムの見学ガイド</small></a>'
                   '<a class="stat" href="/kurobe/"><b>186m</b><small>日本一高い黒部ダム</small></a>'
                   '<a class="stat" href="/keishiki/"><b>約2,700</b><small>日本のダムの数</small></a>'
                   '<a class="stat" href="/dam-card/"><b>800か所以上</b><small>ダムカードの配布</small></a></div>\n' + mm.group(2),
                   s, count=1, flags=re.S)
        m = re.search(r"(<main><div class=\"wrap\">)(.*)(</div></main>)", s, re.S)

    s = s[:m.start(2)] + crumb + hero + main + s[m.end(2):]
    s = s.replace("</head>", MARK + "\n</head>", 1)
    if slug0 and photos:
        s = add_photo(s, slug0, photos)
    s = card_hook(s, rel0)
    open(path, "w", encoding="utf-8").write(s)
    return True


def main():
    dams = []
    tsv = os.path.join(ROOT, "tools", "dams.tsv")
    if os.path.exists(tsv):
        for line in open(tsv, encoding="utf-8").read().splitlines()[1:]:
            c = line.split("\t")
            dams.append((c[2], float(c[4].rstrip("m"))))
        dams.sort(key=lambda x: -x[1])
    photos = load_photos()
    n = 0
    for f in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
        if "/.git/" in f or "/tools/" in f:
            continue
        n += process(f, dams, photos)
    print("decorated", n)


if __name__ == "__main__":
    main()
