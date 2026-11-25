#!/usr/bin/env python3
"""ダム.com のダム個別ページ・ランキング・形式ページ・都道府県一覧を生成する。
データ：tools/dams.tsv（堤高上位50。出典は tabi-mag「日本の巨大ダム 堤高TOP50」、2026-11-25取得。
田子倉ダムの所在地は只見町に修正）。
実行：python3 tools/build.py（リポジトリのルートで）
"""
import csv, html, os, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-11-25"
DATE_JA = "2026年11月25日"
CSS = "/assets/style.css?v=20261125b"

TYPE_SLUG = {"アーチ式コンクリートダム": "arch", "重力式コンクリートダム": "gravity", "ロックフィルダム": "rockfill"}
TYPE_DESC = {
    "arch": "アーチ式コンクリートダムは、上から見ると上流側にふくらんだ弓のような形をしたダムです。水の力をアーチの形で両岸の岩盤に伝えて支えるので、コンクリートの量が少なく、薄くて優美な姿になります。両岸が固い岩でできた、深くて狭い谷に向いています。",
    "gravity": "重力式コンクリートダムは、コンクリートの重さそのもので水の力に耐えるダムです。断面は台形に近く、どっしりとした姿が特徴です。地盤の条件に合わせやすく、日本でいちばん多く造られている形式です。",
    "rockfill": "ロックフィルダムは、岩や石を台形に積み上げて造るダムです。中心部に粘土などの水を通しにくい層を入れて、水をせき止めます。近くで材料の岩が手に入る場所や、地盤がコンクリートダムに向かない場所で造られます。斜面に石が並ぶ、山のような姿が特徴です。",
}
TYPE_NAME = {"arch": "アーチ式コンクリートダム", "gravity": "重力式コンクリートダム", "rockfill": "ロックフィルダム"}

PREF_ORDER = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]

def esc(s):
    return html.escape(s, quote=True)

def page(title, desc, canonical, body, crumbs):
    crumb_html = " › ".join([f'<a href="{u}">{esc(t)}</a>' if u else esc(t) for t, u in crumbs])
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://xn--6ck4c.com{canonical}">
<link rel="stylesheet" href="{CSS}">
</head>
<body>
<header class="site"><div class="wrap">
  <a class="logo" href="/">ダム<span>.com</span></a>
  <nav class="global"><a href="/ranking/">ランキング</a><a href="/pref/">都道府県</a><a href="/dam-card/">ダムカード</a></nav>
</div></header>

<main><div class="wrap">
  <div class="crumb">{crumb_html}</div>
{body}
</div></main>

<footer class="site"><div class="wrap">
  <p>ダム.com は、ダムを巡る人のための個人運営の情報サイトです。国や電力会社など、ダムを管理する団体の公式サイトではありません。</p>
  <p><a href="/">トップ</a> ・ <a href="/ranking/">堤高ランキング</a> ・ <a href="/pref/">都道府県から探す</a> ・ <a href="/keishiki/">ダムの形式</a> ・ <a href="/dam-card/">ダムカード</a></p>
  <p>© 2026 ダム.com</p>
</div></footer>
</body>
</html>
"""

def write(path, content):
    full = os.path.join(ROOT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

def prefs_of(loc):
    return [p for p in PREF_ORDER if p in loc]

SOURCE_HTML = f"""  <section class="sources">
    <h2>出典</h2>
    <ul>
      <li><a href="https://tabi-mag.jp/hugedam-top50/" rel="noopener" target="_blank">ニッポン旅マガジン「日本の巨大ダム 堤高TOP50」</a>（堤高・堤頂長・形式・所在地・水系）</li>
      <li><a href="https://www.mlit.go.jp/river/kankyo/campaign/shunnkan/damcard.html" rel="noopener" target="_blank">国土交通省「ダムカード」</a>（ダムカードの配布場所一覧）</li>
    </ul>
    <p class="updated">最終確認日：{DATE_JA}</p>
  </section>"""

def main():
    rows = []
    with open(os.path.join(ROOT, "tools", "dams.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            r["rank"] = int(r["rank"])
            r["tslug"] = TYPE_SLUG[r["type"]]
            r["prefs"] = prefs_of(r["location"])
            r["url"] = "/kurobe/" if r["slug"] == "kurobe" else f"/dam/{r['slug']}/"
            rows.append(r)
    by_pref = defaultdict(list)
    by_river = defaultdict(list)
    by_type = defaultdict(list)
    for r in rows:
        for p in r["prefs"]:
            by_pref[p].append(r)
        by_river[r["system"]].append(r)
        by_type[r["tslug"]].append(r)

    count = 0
    # 個別ページ
    for r in rows:
        if r["slug"] == "kurobe":
            continue
        name = r["name"]
        lake = f"（ダム湖：{r['lake']}）" if r["lake"] else ""
        same_river = [x for x in by_river[r["system"]] if x is not r]
        same_pref = [x for x in rows if x is not r and set(x["prefs"]) & set(r["prefs"]) and x not in same_river]
        def links(lst):
            return "".join(f'<li><a href="{x["url"]}">{esc(x["name"])}</a>（{esc(x["location"])}・堤高{esc(x["height"])}）</li>' for x in lst)
        related = ""
        if same_river:
            related += f"  <h3>同じ{esc(r['system'])}水系のダム</h3>\n  <ul>{links(same_river)}</ul>\n"
        if same_pref:
            related += f"  <h3>同じ都道府県のダム</h3>\n  <ul>{links(same_pref)}</ul>\n"
        if not related:
            related = "  <p>このサイトで紹介しているダムの一覧は、<a href=\"/ranking/\">堤高ランキング</a>から見られます。</p>\n"
        pref_links = "・".join(f'<a href="/pref/#{esc(p)}">{esc(p)}</a>' for p in r["prefs"])
        lake_p = f"<p>ダムによってできた湖は「{esc(r['lake'])}」と呼ばれています。</p>" if r["lake"] else ""
        body = f"""  <h1>{esc(name)}{esc(lake)}</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>{esc(name)}は、{esc(r['location'])}にある{esc(r['type'])}です。堤高（ダムの高さ）は{esc(r['height'])}で、日本のダムの中で<strong>{r['rank']}番目の高さ</strong>です。{esc(r['system'])}水系の{esc(r['river'])}をせき止めています。</p>

  <h2>基本情報</h2>
  <table>
    <tr><th>所在地</th><td>{esc(r['location'])}（{pref_links}）</td></tr>
    <tr><th>水系・河川</th><td>{esc(r['system'])}水系・{esc(r['river'])}</td></tr>
    <tr><th>形式</th><td><a href="/keishiki/{r['tslug']}/">{esc(r['type'])}</a></td></tr>
    <tr><th>堤高</th><td>{esc(r['height'])}（全国{r['rank']}位）</td></tr>
    <tr><th>堤頂長</th><td>{esc(r['length'])}</td></tr>
    <tr><th>ダム湖</th><td>{esc(r['lake'] or '—')}</td></tr>
  </table>
  <p class="note">堤高は、基礎の岩盤からダムのいちばん上までの高さです。堤頂長は、ダムのいちばん上の部分の長さです。</p>

  <h2>どんなダム？</h2>
  <p>{TYPE_DESC[r['tslug']]}</p>
  {lake_p}

  <h2>見学に行く前に</h2>
  <ul>
    <li><strong>ダムカード</strong>：配っているかどうか、配布の場所と時間は、国土交通省の「ダムカード配布場所一覧」や、ダムを管理する団体の案内で確認してください。→ <a href="/dam-card/">ダムカードのもらい方</a></li>
    <li><strong>道路と季節</strong>：山の中のダムは、冬に道路が通れなくなったり、見学できる場所が閉まったりすることがあります</li>
    <li><strong>見学できる場所</strong>：ダムの上（天端）を歩けるか、資料館があるかはダムによって違います。工事などで立ち入りが制限されることもあります</li>
  </ul>

  <h2>あわせて見たいダム</h2>
{related}
{SOURCE_HTML}"""
        title = f"{name}｜堤高{r['height']}・全国{r['rank']}位の{r['type']}（{'・'.join(r['prefs'])}）｜ダム.com"
        desc = f"{name}（{r['location']}）は堤高{r['height']}で全国{r['rank']}位の{r['type']}。基本情報、ダムの形式、ダム湖、見学前の注意点、近くのダムをまとめました。"
        write(r["url"], page(title, desc, r["url"], body, [("ダム.com", "/"), ("堤高ランキング", "/ranking/"), (name, None)]))
        count += 1

    # ランキング
    trs = "".join(f'<tr><td>{r["rank"]}</td><td><a href="{r["url"]}">{esc(r["name"])}</a></td><td>{esc(r["height"])}</td><td><a href="/keishiki/{r["tslug"]}/">{esc(TYPE_NAME[r["tslug"]].replace("コンクリートダム","").replace("ダム",""))}</a></td><td>{esc(r["location"])}</td></tr>' for r in rows)
    body = f"""  <h1>日本のダム 高さ（堤高）ランキング TOP50</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>日本のダムを、堤高（基礎の岩盤からダムのいちばん上までの高さ）の順に並べました。1位は富山県の黒部ダムで、高さは186mです。ダム名を押すと、それぞれのダムの詳しいページを見られます。</p>
  <table>
    <thead><tr><th>順位</th><th>ダム名</th><th>堤高</th><th>形式</th><th>所在地</th></tr></thead>
    <tbody>{trs}</tbody>
  </table>
  <h2>ランキングからわかること</h2>
  <ul>
    <li>上位50のうち、アーチ式が{len(by_type['arch'])}、重力式が{len(by_type['gravity'])}、ロックフィルが{len(by_type['rockfill'])}です</li>
    <li>利根川、木曽川、信濃川の水系に、高いダムが多く集まっています</li>
  </ul>
{SOURCE_HTML}"""
    write("/ranking/", page("日本のダム 高さ（堤高）ランキングTOP50｜ダム.com", "日本のダムを堤高の順に50位まで並べたランキングです。1位は黒部ダムの186m。形式・所在地つきで、各ダムの詳しいページにリンクしています。", "/ranking/", body, [("ダム.com", "/"), ("堤高ランキング", None)]))
    count += 1

    # 形式ページ
    cards = ""
    for ts in ["arch", "gravity", "rockfill"]:
        lst = by_type[ts]
        items = "".join(f'<li><a href="{x["url"]}">{esc(x["name"])}</a>（{esc(x["height"])}・{esc(x["location"])}）</li>' for x in lst)
        body = f"""  <h1>{TYPE_NAME[ts]}とは｜特徴と代表的なダム</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>{TYPE_DESC[ts]}</p>
  <h2>見分け方のポイント</h2>
  {"<p>上から見て、ダムが上流に向かって弓なりに曲がっていればアーチ式です。下流から見上げると、壁が薄く、両側の山に食い込むように見えます。</p>" if ts=="arch" else ("<p>ダムの壁がまっすぐで、下流側が急な斜面のコンクリートになっています。横から見ると、厚みのある台形をしています。</p>" if ts=="gravity" else "<p>コンクリートの壁ではなく、岩や石が積まれたなだらかな斜面に見えます。ダムというより、大きな土手や山のように見えるのが特徴です。</p>")}
  <h2>高さ上位50に入っている{TYPE_NAME[ts]}（{len(lst)}基）</h2>
  <ul>{items}</ul>
  <p>ほかの形式は<a href="/keishiki/">ダムの形式の見分け方</a>で紹介しています。</p>
{SOURCE_HTML}"""
        write(f"/keishiki/{ts}/", page(f"{TYPE_NAME[ts]}とは｜特徴・見分け方・代表的なダム｜ダム.com", f"{TYPE_NAME[ts]}の仕組みと見分け方、日本の高いダムのうちこの形式のダムをまとめました。", f"/keishiki/{ts}/", body, [("ダム.com", "/"), ("ダムの形式", "/keishiki/"), (TYPE_NAME[ts], None)]))
        count += 1
        cards += f'<a class="card" href="/keishiki/{ts}/"><strong>{TYPE_NAME[ts]}</strong><small>上位50のうち{len(lst)}基</small></a>'
    body = f"""  <h1>ダムの形式の見分け方</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>ダムは、水をせき止める仕組みによっていくつかの形式に分かれます。形式がわかると、ダム巡りで見た目の違いを楽しめます。日本の大きなダムで多いのは、次の3つです。</p>
  <div class="cards">{cards}</div>
  <h2>ほかの形式</h2>
  <ul>
    <li><strong>中空重力式</strong>：重力式の中を空洞にして、コンクリートの量を減らしたもの</li>
    <li><strong>アースダム</strong>：土を盛って造るダム。ため池などに多い形式です</li>
    <li><strong>台形CSGダム</strong>：現地の土砂にセメントと水をまぜた材料で、台形に造る比較的新しい形式です</li>
  </ul>
{SOURCE_HTML}"""
    write("/keishiki/", page("ダムの形式の見分け方｜アーチ式・重力式・ロックフィル｜ダム.com", "ダムの主な形式（アーチ式、重力式、ロックフィル）の違いと見分け方を、日本の高いダムの例とあわせて紹介します。", "/keishiki/", body, [("ダム.com", "/"), ("ダムの形式", None)]))
    count += 1

    # 都道府県一覧
    secs = ""
    for p in PREF_ORDER:
        if p not in by_pref:
            continue
        items = "".join(f'<li><a href="{x["url"]}">{esc(x["name"])}</a>（堤高{esc(x["height"])}・全国{x["rank"]}位）</li>' for x in by_pref[p])
        secs += f'  <h2 id="{esc(p)}">{esc(p)}</h2>\n  <ul>{items}</ul>\n'
    body = f"""  <h1>都道府県から探す</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>このサイトで紹介しているダムを、都道府県ごとにまとめました。2つの県にまたがるダムは、両方に載せています。</p>
{secs}
{SOURCE_HTML}"""
    write("/pref/", page("都道府県から探す｜全国の高いダム一覧｜ダム.com", "日本の高いダムを都道府県ごとにまとめました。各ダムの高さ・形式・見学前の注意点のページにリンクしています。", "/pref/", body, [("ダム.com", "/"), ("都道府県から探す", None)]))
    count += 1

    # sitemap
    urls = ["/", "/dam-card/", "/kurobe/", "/ranking/", "/keishiki/", "/pref/"] + [f"/keishiki/{t}/" for t in ["arch","gravity","rockfill"]] + [r["url"] for r in rows if r["slug"] != "kurobe"]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>https://xn--6ck4c.com{u}</loc><lastmod>{DATE}</lastmod></url>\n" for u in urls) + "</urlset>\n"
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    print("generated", count, "pages; sitemap urls", len(urls))

if __name__ == "__main__":
    main()
