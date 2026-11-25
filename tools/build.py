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


TYPE_EXTRA = {
"arch": """  <h2>仕組みをもう少し詳しく</h2>
  <p>アーチ式ダムは、石造りの橋やトンネルの入口と同じ「アーチ」の原理を使っています。ダム湖の水はダムを下流へ押しますが、上流側にふくらんだ弓の形をしていると、その力はダムの中を通って左右の岩盤へと流れていきます。つまり、アーチ式ダムを支えているのはダムそのものの重さではなく、<strong>両岸の山の岩盤</strong>です。そのため、両岸が固い岩でできていることが、アーチ式を造るための絶対の条件になります。</p>
  <p>このため、アーチ式ダムを造る前には、両岸の岩の固さやひび割れの様子を、ボーリングや試験で念入りに調べます。ダムの壁と岩盤がつながる部分は、ダム全体の力を受け止める大切な場所です。</p>
  <p>アーチ式の中には、横から見たときにも上流側にふくらんだ形をした「ドーム型アーチ」もあります。縦と横の両方向にアーチの効果をもたせることで、さらに薄く造ることができます。</p>

  <h2>長所と短所</h2>
  <table>
    <tr><th>長所</th><td>使うコンクリートの量が少なくて済む。深くて狭い谷に、とても高いダムを造れる。曲線の姿が美しい</td></tr>
    <tr><th>短所</th><td>両岸が固い岩盤の場所でしか造れない。形が複雑なので、設計と工事に高い技術が必要</td></tr>
  </table>

  <h2>日本のアーチ式ダムの特徴</h2>
  <p>日本でいちばん高いダムである<a href="/kurobe/">黒部ダム</a>（186m）はアーチ式です。黒部峡谷のように、固い岩に囲まれた深いV字の谷は、アーチ式にぴったりの場所でした。日本の高いダム上位50の中では、北アルプスや飛騨、群馬・栃木の山奥など、険しい峡谷にあるダムにアーチ式が多く見られます。</p>

  <h2>見学のポイント</h2>
  <ul>
    <li><strong>ダムの下から見上げる</strong>：薄い壁が頭の上に覆いかぶさってくるように見え、アーチ式ならではの迫力があります</li>
    <li><strong>ダムの上を歩く</strong>：天端のカーブを足元で感じられます。端に立つと、反対側の端が弓なりに見えます</li>
    <li><strong>両岸の岩を見る</strong>：ダムが岩盤にしっかり食い込んでいる様子がわかると、アーチ式の仕組みが実感できます</li>
  </ul>

  <h2>よくある質問</h2>
  <dl>
    <dt><strong>日本でいちばん高いアーチ式ダムは？</strong></dt>
    <dd>富山県の黒部ダムで、高さは186mです。アーチ式であるだけでなく、すべての形式を合わせても日本一高いダムです。2番目は広島県の温井ダム（156m）、3番目は長野県の奈川渡ダム（155m）です。</dd>
    <dt><strong>アーチ式ダムはどこに多いですか？</strong></dt>
    <dd>固い岩に囲まれた、深くて狭い谷がある山奥に多く造られています。上位50では、長野県、栃木県、群馬県、岐阜県などの山あいに見られます。</dd>
    <dt><strong>薄くて壊れないのですか？</strong></dt>
    <dd>水の力をアーチの形で両岸の岩盤に伝えるので、厚みがなくても水を支えられます。岩盤の強さを細かく調べたうえで設計されています。</dd>
    <dt><strong>重力式アーチダムとの違いは？</strong></dt>
    <dd>重力式アーチダムは、アーチの効果に加えて、ダムの重さでも水を支える形式です。純粋なアーチ式より厚く造られます。</dd>
  </dl>
""",
"gravity": """  <h2>仕組みをもう少し詳しく</h2>
  <p>重力式コンクリートダムは、名前のとおり<strong>コンクリートの重さ（重力）</strong>で水の力に耐えるダムです。ダム湖の水はダムを下流へ押し倒そうとしますが、ダムが十分に重く、地面との間で踏ん張れるように、底の幅を広くとった台形の断面に造られています。ダム1本1本の区画が、それぞれ自分の重さで立っているイメージです。</p>
  <p>アーチ式のように両岸の岩盤に頼らないので、地盤の条件に合わせやすく、さまざまな場所で造ることができます。そのかわり、使うコンクリートの量は多くなります。</p>

  <h2>長所と短所</h2>
  <table>
    <tr><th>長所</th><td>仕組みが単純で、安全性を確かめやすい。いろいろな地盤に合わせて造れる。ダムの上に洪水吐きのゲートを設けやすい</td></tr>
    <tr><th>短所</th><td>大量のコンクリートが必要になる。工事の規模が大きくなりやすい</td></tr>
  </table>

  <h2>日本の重力式ダムの特徴</h2>
  <p>重力式は、日本でいちばん多く造られている形式です。日本の高いダム上位50の中でも数が多く、首都圏の水がめとなっている<a href="/dam/miyagase/">宮ヶ瀬ダム</a>（156m）や、東京の奥多摩湖をつくる小河内ダム（148m）、天竜川で発電を担う佐久間ダム（155.5m）などがこの形式です。</p>

  <h2>見学のポイント</h2>
  <ul>
    <li><strong>洪水吐きのゲート</strong>：ダムの上や中ほどに並ぶゲートは、重力式ダムの顔ともいえる部分です</li>
    <li><strong>観光放流</strong>：急な下流面を水が流れ落ちる様子や、ダムの途中から噴き出す放流は迫力があります。宮ヶ瀬ダムでは4月〜11月に定期の観光放流があります</li>
    <li><strong>下流面の角度</strong>：横から見ると、上流側はほぼ垂直、下流側は一定の角度の急な斜面になっている台形の形がわかります</li>
    <li><strong>ダムの内部</strong>：重力式ダムの中には点検用の通路（監査廊）があり、見学会で中に入れることがあります</li>
  </ul>

  <h2>よくある質問</h2>
  <dl>
    <dt><strong>日本でいちばん高い重力式ダムは？</strong></dt>
    <dd>福島県と新潟県の境にある奥只見ダムで、高さは157mです。</dd>
    <dt><strong>中空重力式との違いは？</strong></dt>
    <dd>中空重力式は、ダムの中を空洞にしてコンクリートの量を減らした形式です。外から見ると似ていますが、中が大きな空間になっています。</dd>
    <dt><strong>なぜ日本に多いのですか？</strong></dt>
    <dd>地盤の条件に合わせやすく、大雨のときに水を流す洪水吐きを設けやすいため、洪水が多い日本の川に向いているからです。</dd>
  </dl>
""",
"rockfill": """  <h2>仕組みをもう少し詳しく</h2>
  <p>ロックフィルダムは、岩（ロック）を積み上げて（フィル）造るダムです。岩を積み上げただけでは水が漏れてしまうので、ダムの中に<strong>水を通しにくい層</strong>を入れます。多いのは、ダムの中心に粘土などで「コア」と呼ばれる壁を造り、その両側を砂利や岩で包むように固める形です。コアの代わりに、上流側の表面をアスファルトやコンクリートで覆って水を止める形もあります。</p>
  <p>ダムの中は、中心の水を通しにくいコア、そのまわりの細かい砂利の層（フィルター）、いちばん外側の大きな岩の層というように、材料を場所ごとに分けて積み上げています。フィルターの層は、コアの細かい土が水と一緒に流れ出してしまうのを防ぐ大切な役割を持っています。</p>
  <p>大量の岩を積み上げた重さでダム全体が安定するので、断面はとても幅の広い台形になります。高さに比べて底の幅が何倍にもなり、遠くから見ると山や大きな土手のように見えます。</p>

  <h2>長所と短所</h2>
  <table>
    <tr><th>長所</th><td>材料の岩を近くの山から取れれば、遠くから運ぶ必要がない。コンクリートダムに向かない地盤でも造れる。幅の広い谷にも対応できる</td></tr>
    <tr><th>短所</th><td>体積がとても大きくなる。ダムの上を水が越えると壊れやすいため、洪水吐きを別に設ける必要がある</td></tr>
  </table>

  <h2>日本のロックフィルダムの特徴</h2>
  <p>長野県大町市の高瀬ダムは、高さ176mで日本で2番目に高いダムであり、ロックフィルダムとしては日本一の高さです。岐阜県の徳山ダムは、ためられる水の量（総貯水容量）が日本一のダムとして知られています。岩手県の胆沢ダムは、日本の高いダム上位50の中でいちばん長く、堤頂長は723mあります。</p>

  <h2>見学のポイント</h2>
  <ul>
    <li><strong>斜面の石</strong>：近くで見ると、一つ一つの石の大きさに驚かされます。きれいに並べられた石の模様も見どころです</li>
    <li><strong>ダムの長さ</strong>：ロックフィルは長いダムが多く、ダムの上を端から端まで歩くとかなりの距離があります</li>
    <li><strong>洪水吐き</strong>：ダム本体とは別の場所に、コンクリートの洪水吐きが造られています。どこにあるか探してみましょう</li>
    <li><strong>ダム湖との景色</strong>：なだらかな斜面と、広いダム湖を一緒に見渡せる景色が魅力です</li>
  </ul>

  <h2>よくある質問</h2>
  <dl>
    <dt><strong>日本でいちばん高いロックフィルダムは？</strong></dt>
    <dd>長野県大町市の高瀬ダムで、高さは176mです。すべての形式を合わせても、黒部ダムに次ぐ日本で2番目の高さです。</dd>
    <dt><strong>アースダムとの違いは？</strong></dt>
    <dd>主な材料が岩ならロックフィル、土ならアースダムです。アースダムは、農業用のため池などに多い形式です。</dd>
    <dt><strong>なぜロックフィルの観光放流は少ないのですか？</strong></dt>
    <dd>ロックフィルは、ダムの上を水が流れると壊れやすいため、水はダム本体ではなく別に造った洪水吐きから流します。そのため、コンクリートダムのようにダムの壁から水が噴き出す放流は見られません。</dd>
  </dl>
""",
}

TYPE_FEATURED = {
"arch": """  <h2>代表的なアーチ式ダム</h2>
  <h3>黒部ダム（富山県・186m）</h3>
  <p>日本一高いダムで、アーチ式の代表です。黒部峡谷の深い谷に、長さ492mの弓なりの壁が架かっています。夏から秋の観光放水が有名で、立山黒部アルペンルートの途中で見学できます。→ <a href="/kurobe/">黒部ダムの観光放水と行き方</a></p>
  <h3>温井ダム（広島県・156m）</h3>
  <p>広島県安芸太田町の滝山川にあるアーチ式ダムで、アーチ式では黒部ダムに次ぐ高さです。日本の高いダム上位50に入っているアーチ式の中では、西日本でいちばん高いダムです。ダム湖は龍姫湖と呼ばれています。</p>
  <h3>奈川渡ダム（長野県・155m）</h3>
  <p>長野県松本市の犀川（梓川）にあるアーチ式ダムで、ダム湖は梓湖です。北アルプスから流れ出る川の深い谷に造られています。</p>
  <h3>川治ダムと川俣ダム（栃木県）</h3>
  <p>栃木県日光市の鬼怒川には、上位50に入るアーチ式ダムが2つあります。川治ダム（140m）と、その上流の川俣ダム（117m）です。川俣ダムは高さ117mに対して堤頂長が131mしかなく、深くて狭い谷に造られたアーチ式の特徴がよく表れています。</p>
  <h3>矢木沢ダム（群馬県・131m）</h3>
  <p>群馬県みなかみ町の利根川にあるアーチ式ダムで、ダム湖は奥利根湖です。首都圏の水を支える利根川の、上流の山奥に造られています。</p>
  <h3>真名川ダムと新豊根ダム</h3>
  <p>福井県大野市の真名川ダム（127.5m、麻那姫湖）と、愛知県豊根村の新豊根ダム（116.5m、みどり湖）も、上位50に入るアーチ式です。アーチ式は北アルプス周辺だけでなく、北陸や東海の山あいにも造られています。</p>
  <h3>一ツ瀬ダム（宮崎県・130m）</h3>
  <p>宮崎県西都市の一ツ瀬川にあるアーチ式ダムで、九州で上位50に入っているアーチ式はこのダムです。ダム湖は米良湖と呼ばれています。</p>
""",
"gravity": """  <h2>代表的な重力式ダム</h2>
  <h3>奥只見ダムと田子倉ダム（福島県・新潟県）</h3>
  <p>只見川には、上位50に入る重力式ダムが2つあります。福島県と新潟県の境にある奥只見ダム（157m）は、上位50の重力式の中でいちばん高いダムです。その下流の田子倉ダム（145m）も、長さ462mの大きなダムです。</p>
  <h3>小河内ダム（東京都・148m）</h3>
  <p>東京都奥多摩町の多摩川にあるダムで、ダム湖は奥多摩湖です。1957年に完成した、東京の水がめとして知られるダムです。</p>
  <h3>佐久間ダム（静岡県・愛知県・155.5m）</h3>
  <p>静岡県浜松市と愛知県豊根村の境、天竜川にあるダムで、1956年に完成しました。ダム湖は佐久間湖です。天竜川の豊かな水を使って発電するために造られた、重力式の大きなダムです。</p>
  <h3>宮ヶ瀬ダム（神奈川県・156m）</h3>
  <p>2000年に完成した、首都圏最大級のダムです。資料館やインクラインがあり、4月〜11月には定期の観光放流も行われる、見学しやすい重力式ダムです。→ <a href="/dam/miyagase/">宮ヶ瀬ダムの観光放流と行き方</a></p>
  <h3>浦山ダムと滝沢ダム（埼玉県）</h3>
  <p>埼玉県秩父市には、荒川水系に上位50の重力式ダムが2つあります。浦山ダム（156m、秩父さくら湖）と滝沢ダム（132m、奥秩父もみじ湖）です。</p>
""",
"rockfill": """  <h2>代表的なロックフィルダム</h2>
  <h3>高瀬ダムと七倉ダム（長野県大町市）</h3>
  <p>北アルプスから流れる高瀬川には、上位50に入るロックフィルダムが2つ並んでいます。上流の高瀬ダム（176m）はロックフィルで日本一の高さ、下流の七倉ダム（125m）も大きなロックフィルダムです。</p>
  <h3>徳山ダム（岐阜県・161m）</h3>
  <p>岐阜県揖斐川町の揖斐川にあるダムで、ダム湖は徳山湖です。高さは日本で3番目、ためられる水の量（総貯水容量）は日本一のダムとして知られています。</p>
  <h3>胆沢ダム（岩手県・127m）</h3>
  <p>岩手県奥州市の胆沢川にあるダムで、ダム湖は奥州湖です。堤頂長は723mで、日本の高いダム上位50の中でいちばん長いダムです。ロックフィルが幅の広い谷にも造れることがよくわかるダムです。</p>
  <h3>奈良俣ダム（群馬県・158m）</h3>
  <p>群馬県みなかみ町の楢俣川にあるダムで、ダム湖はならまた湖です。上位50の中で、高瀬ダム、徳山ダムに次ぐ高さのロックフィルです。</p>
  <h3>小石原川ダム（福岡県・139m）</h3>
  <p>福岡県朝倉市の小石原川にあるダムで、ダム湖は令和あさくら湖です。2021年に運用が始まった新しいダムで、九州で上位50に入るダムの中ではいちばん高いダムです。</p>
""",
}

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
  <nav class="global"><a href="/ranking/">ランキング</a><a href="/houryu/">観光放流</a><a href="/keishiki/">ダムの形式</a><a href="/dam-card/">ダムカード</a></nav>
</div></header>

<main><div class="wrap">
  <div class="crumb">{crumb_html}</div>
{body}
</div></main>

<footer class="site"><div class="wrap">
  <p>ダム.com は、ダムを巡る人のための個人運営の情報サイトです。国や電力会社など、ダムを管理する団体の公式サイトではありません。</p>
  <p><a href="/">トップ</a> ・ <a href="/ranking/">堤高ランキング</a> ・ <a href="/houryu/">観光放流カレンダー</a> ・ <a href="/keishiki/">ダムの形式</a> ・ <a href="/dam-card/">ダムカード</a></p>
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

DETAILED = set()
_dp = os.path.join(ROOT, "tools", "detailed.txt")
if os.path.exists(_dp):
    DETAILED = {l.strip() for l in open(_dp, encoding="utf-8") if l.strip() and not l.startswith("#")}

def dam_link(r):
    return f'<a href="{r["url"]}">{esc(r["name"])}</a>' if r["has_page"] else esc(r["name"])

def main():
    rows = []
    with open(os.path.join(ROOT, "tools", "dams.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            r["rank"] = int(r["rank"])
            r["tslug"] = TYPE_SLUG[r["type"]]
            r["prefs"] = prefs_of(r["location"])
            r["url"] = "/kurobe/" if r["slug"] == "kurobe" else f"/dam/{r['slug']}/"
            r["has_page"] = r["slug"] == "kurobe" or r["slug"] in DETAILED
            rows.append(r)
    # 堤高順に順位を振り直す（同じ高さは元の並び順）
    rows.sort(key=lambda x: (-float(x["height"].rstrip("m")), x["rank"]))
    for i, x in enumerate(rows, 1):
        x["rank"] = i
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
        if not r["has_page"] or r["slug"] == "kurobe" or r["slug"] in DETAILED:
            continue  # 詳しいページは手書き（dam/<slug>/index.html）
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

    # 手書き本文（tools/bodies/<slug>.html の1行目が title、2行目が description、3行目以降が本文）
    for r in rows:
        bp = os.path.join(ROOT, "tools", "bodies", r["slug"] + ".html")
        if r["slug"] in DETAILED and os.path.exists(bp):
            lines = open(bp, encoding="utf-8").read().split("\n", 2)
            write(r["url"], page(lines[0], lines[1], r["url"], lines[2], [("ダム.com", "/"), ("堤高ランキング", "/ranking/"), (r["name"], None)]))
            count += 1

    # ランキング
    trs = "".join(f'<tr><td>{r["rank"]}</td><td>{dam_link(r)}</td><td>{esc(r["height"])}</td><td><a href="/keishiki/{r["tslug"]}/">{esc(TYPE_NAME[r["tslug"]].replace("コンクリートダム","").replace("ダム",""))}</a></td><td>{esc(r["location"])}</td></tr>' for r in rows)
    def h(x): return float(x["height"].rstrip("m"))
    def ln(x): return float(x["length"].rstrip("m"))
    sys_cnt = sorted(by_river.items(), key=lambda kv: -len(kv[1]))[:5]
    sys_rows = "".join(f'<tr><td>{esc(k)}水系</td><td>{len(v)}基</td><td>{"、".join(esc(x["name"]) for x in v[:6])}{"ほか" if len(v)>6 else ""}</td></tr>' for k, v in sys_cnt)
    pref_cnt = sorted(by_pref.items(), key=lambda kv: -len(kv[1]))[:8]
    pref_rows = "".join(f'<tr><td>{esc(k)}</td><td>{len(v)}基</td><td>{"、".join(esc(x["name"]) for x in v)}</td></tr>' for k, v in pref_cnt)
    longest = sorted(rows, key=lambda x: -ln(x))[:5]
    long_rows = "".join(f'<tr><td>{dam_link(x)}</td><td>{esc(x["length"])}</td><td>{esc(x["height"])}（{x["rank"]}位）</td><td>{esc(TYPE_NAME[x["tslug"]])}</td></tr>' for x in longest)
    type_top = "".join(f'<li><strong>{TYPE_NAME[t]}</strong>でいちばん高いのは{dam_link(by_type[t][0])}（{esc(by_type[t][0]["height"])}・{esc(by_type[t][0]["location"])}）</li>' for t in ["arch","gravity","rockfill"])
    hokkaido = [x for x in rows if "北海道" in x["prefs"]]
    kyushu = [x for x in rows if set(x["prefs"]) & {"福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県"}]
    extra = f"""  <h2>堤高とは？</h2>
  <p>ダムの大きさを表す数字はいくつかありますが、いちばんよく使われるのが<strong>堤高（ていこう）</strong>です。堤高は、ダムの基礎になっている岩盤から、ダムのいちばん上（天端）までの高さのことです。地面から見える部分だけでなく、地中に埋まっている基礎の部分も含むため、実際に下から見上げたときの高さより大きな数字になることがあります。</p>
  <p>法律や国の基準では、堤高が15m以上のものを「ダム」と呼びます。日本には、この基準を満たすダムが数千あります。ランキングの50位でも堤高は100mを超えていて、上位のダムがいかに大きいかがわかります。</p>

  <h2>形式ごとのいちばん高いダム</h2>
  <ul>{type_top}</ul>
  <p>上位では、コンクリートを使うアーチ式・重力式と、岩を積み上げるロックフィルがほぼ同じくらいの数を占めています。深くて狭い谷にはアーチ式、地盤や材料の条件に合わせて重力式やロックフィルと、場所に合った形式が選ばれています。形式の違いは<a href="/keishiki/">ダムの形式の見分け方</a>で詳しく紹介しています。</p>

  <h2>高いダムが多い水系</h2>
  <table>
    <thead><tr><th>水系</th><th>上位50の数</th><th>主なダム</th></tr></thead>
    <tbody>{sys_rows}</tbody>
  </table>
  <p>利根川水系には、首都圏の水がめとなる大きなダムが集まっています。木曽川水系や信濃川水系は、北アルプスなどの高い山から流れ出る川で、深い谷に高いダムが造られてきました。</p>

  <h2>高いダムが多い都道府県</h2>
  <table>
    <thead><tr><th>都道府県</th><th>上位50の数</th><th>ダム</th></tr></thead>
    <tbody>{pref_rows}</tbody>
  </table>
  <p>2つの県にまたがるダムは、両方の県で数えています。北海道で上位50に入っているのは{len(hokkaido)}基、九州では{len(kyushu)}基で、高いダムは本州の中部・関東の山あいに集中していることがわかります。</p>

  <h2>上位50の中で長さ（堤頂長）が長いダム</h2>
  <p>堤頂長は、ダムのいちばん上の部分の長さです。高さとはまた違った迫力があり、長いダムはダムの上を歩くと端から端まで数分かかります。</p>
  <table>
    <thead><tr><th>ダム名</th><th>堤頂長</th><th>堤高（順位）</th><th>形式</th></tr></thead>
    <tbody>{long_rows}</tbody>
  </table>
  <p>長いダムにロックフィルが多いのは、岩を台形に積み上げる形式のため、谷の幅が広い場所にも造りやすいからです。</p>

  <h2>見学しやすい高いダム</h2>
  <p>高いダムの多くは山奥にありますが、観光地として整備されていて、気軽に見学できるダムもあります。</p>
  <ul>
    <li><a href="/kurobe/">黒部ダム</a>（1位）：立山黒部アルペンルートの途中にあり、夏から秋に観光放水が行われます。冬は行けません</li>
    <li><a href="/dam/miyagase/">宮ヶ瀬ダム</a>（7位）：都心から車で約1時間。4月〜11月は定期の観光放流があり、資料館やインクラインもあります</li>
  </ul>
  <p>そのほかのダムも、見学情報を調べたものから順にページを追加していきます。</p>
"""
    body = f"""  <h1>日本のダム 高さ（堤高）ランキング TOP50</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>日本のダムを、堤高（基礎の岩盤からダムのいちばん上までの高さ）の順に並べました。1位は富山県の黒部ダムで、高さは186mです。詳しいページがあるダムは、ダム名から開けます。ページは、ダムごとの見学情報を調べたものから順に追加しています。</p>
  <table>
    <thead><tr><th>順位</th><th>ダム名</th><th>堤高</th><th>形式</th><th>所在地</th></tr></thead>
    <tbody>{trs}</tbody>
  </table>
  <h2>ランキングからわかること</h2>
  <ul>
    <li>上位50のうち、アーチ式が{len(by_type['arch'])}、重力式が{len(by_type['gravity'])}、ロックフィルが{len(by_type['rockfill'])}です</li>
    <li>利根川、木曽川、信濃川の水系に、高いダムが多く集まっています</li>
  </ul>
{extra}
{SOURCE_HTML}"""
    write("/ranking/", page("日本のダム 高さ（堤高）ランキングTOP50｜ダム.com", "日本のダムを堤高の順に50位まで並べたランキングです。1位は黒部ダムの186m。形式・所在地つきで、各ダムの詳しいページにリンクしています。", "/ranking/", body, [("ダム.com", "/"), ("堤高ランキング", None)]))
    count += 1

    # 形式ページ
    cards = ""
    for ts in ["arch", "gravity", "rockfill"]:
        lst = by_type[ts]
        items = "".join(f'<tr><td>{x["rank"]}位</td><td>{dam_link(x)}</td><td>{esc(x["height"])}</td><td>{esc(x["length"])}</td><td>{esc(x["location"])}</td><td>{esc(x["system"])}水系・{esc(x["river"])}</td><td>{esc(x["lake"] or "—")}</td></tr>' for x in lst)
        hs = [float(x["height"].rstrip("m")) for x in lst]; ls = [float(x["length"].rstrip("m")) for x in lst]
        lmax = max(lst, key=lambda x: float(x["length"].rstrip("m"))); lmin = min(lst, key=lambda x: float(x["length"].rstrip("m")))
        ratio = sum(l/h for l, h in zip(ls, hs))/len(lst)
        stats = f"""  <h2>数字で見る{TYPE_NAME[ts]}</h2>
  <p>日本の高いダム上位50に入っている{TYPE_NAME[ts]}は{len(lst)}基です。この{len(lst)}基の高さの平均は約{sum(hs)/len(hs):.0f}m、堤頂長（ダムのいちばん上の長さ）の平均は約{sum(ls)/len(ls):.0f}mです。</p>
  <p>いちばん長いのは{esc(lmax["name"])}の{esc(lmax["length"])}、いちばん短いのは{esc(lmin["name"])}の{esc(lmin["length"])}です。堤頂長を高さで割ると、平均で約{ratio:.1f}倍になります。この数字が大きいほど、高さに比べて横に長いダムということです。{"アーチ式は狭い谷に造るので、高さのわりに短いダムが多いのが特徴です。" if ts=="arch" else ("重力式は、アーチ式より横に長く、ロックフィルより短い、中間の形のダムが多くなっています。" if ts=="gravity" else "ロックフィルは幅の広い谷にも造れるので、高さのわりに長いダムが多いのが特徴です。")}</p>
"""
        body = f"""  <h1>{TYPE_NAME[ts]}とは｜特徴と代表的なダム</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>{TYPE_DESC[ts]}</p>
  <h2>見分け方のポイント</h2>
  {"<p>上から見て、ダムが上流に向かって弓なりに曲がっていればアーチ式です。下流から見上げると、壁が薄く、両側の山に食い込むように見えます。</p>" if ts=="arch" else ("<p>ダムの壁がまっすぐで、下流側が急な斜面のコンクリートになっています。横から見ると、厚みのある台形をしています。</p>" if ts=="gravity" else "<p>コンクリートの壁ではなく、岩や石が積まれたなだらかな斜面に見えます。ダムというより、大きな土手や山のように見えるのが特徴です。</p>")}
{TYPE_EXTRA[ts]}
{TYPE_FEATURED[ts]}
{stats}
  <h2>高さ上位50に入っている{TYPE_NAME[ts]}（{len(lst)}基）</h2>
  <table>
    <thead><tr><th>順位</th><th>ダム名</th><th>堤高</th><th>堤頂長</th><th>所在地</th><th>水系・河川</th><th>ダム湖</th></tr></thead>
    <tbody>{items}</tbody>
  </table>
  <p>ほかの形式は<a href="/keishiki/">ダムの形式の見分け方</a>で紹介しています。</p>
{SOURCE_HTML}"""
        write(f"/keishiki/{ts}/", page(f"{TYPE_NAME[ts]}とは｜特徴・見分け方・代表的なダム｜ダム.com", f"{TYPE_NAME[ts]}の仕組みと見分け方、日本の高いダムのうちこの形式のダムをまとめました。", f"/keishiki/{ts}/", body, [("ダム.com", "/"), ("ダムの形式", "/keishiki/"), (TYPE_NAME[ts], None)]))
        count += 1
        cards += f'<a class="card" href="/keishiki/{ts}/"><strong>{TYPE_NAME[ts]}</strong><small>上位50のうち{len(lst)}基</small></a>'
    rep = ""
    for t in ["arch","gravity","rockfill"]:
        lst = by_type[t][:6]
        rep += f'  <h3>{TYPE_NAME[t]}（高さ上位50のうち{len(by_type[t])}基）</h3>\n  <ul>' + "".join(f'<li>{dam_link(x)}：{esc(x["location"])}、堤高{esc(x["height"])}・全国{x["rank"]}位、堤頂長{esc(x["length"])}</li>' for x in lst) + '</ul>\n'
    body = f"""  <h1>ダムの形式の見分け方</h1>
  <p class="updated">最終確認日：{DATE_JA}</p>
  <p>ダムは、水をせき止める仕組みによっていくつかの「形式」に分かれます。形式がわかると、ダムを見たときに「なぜこの形なのか」がわかり、ダム巡りがぐっと楽しくなります。日本の大きなダムで多いのは、アーチ式、重力式、ロックフィルの3つです。</p>
  <div class="cards">{cards}</div>

  <h2>3つの形式をくらべる</h2>
  <table>
    <thead><tr><th></th><th>アーチ式</th><th>重力式</th><th>ロックフィル</th></tr></thead>
    <tbody>
      <tr><th>材料</th><td>コンクリート</td><td>コンクリート</td><td>岩・石・粘土</td></tr>
      <tr><th>水を支える仕組み</th><td>弓の形で水の力を両岸の岩盤に伝える</td><td>コンクリートの重さで支える</td><td>積み上げた岩の重さと、中心の水を通さない層で止める</td></tr>
      <tr><th>上から見た形</th><td>上流側にふくらんだ弓形</td><td>ほぼまっすぐ</td><td>ほぼまっすぐで幅が広い</td></tr>
      <tr><th>横から見た形</th><td>薄い</td><td>台形（どっしり）</td><td>なだらかな台形（山のよう）</td></tr>
      <tr><th>向いている場所</th><td>両岸が固い岩の、深くて狭い谷</td><td>さまざまな地盤</td><td>材料の岩が近くで取れる場所、幅の広い谷</td></tr>
      <tr><th>代表的なダム</th><td><a href="/kurobe/">黒部ダム</a></td><td><a href="/dam/miyagase/">宮ヶ瀬ダム</a></td><td>高瀬ダム、徳山ダム</td></tr>
    </tbody>
  </table>

  <h2>現地での見分け方</h2>
  <h3>1. まず材料を見る</h3>
  <p>ダムの表面が灰色のコンクリートなら、アーチ式か重力式です。岩や石がごろごろと並んだ斜面なら、ロックフィルです。ロックフィルは、遠くから見るとダムというより大きな土手や山のように見えます。</p>
  <h3>2. コンクリートなら、上から見た形を見る</h3>
  <p>ダムの上（天端）が、上流側に向かって弓のように曲がっていればアーチ式です。ほぼまっすぐなら重力式です。地図アプリの航空写真で上から見ると、違いがはっきりわかります。</p>
  <h3>3. 下流側の面の角度を見る</h3>
  <p>重力式は、下流側の面が一定の角度の急な斜面になっていて、横から見ると台形です。アーチ式は壁が薄く、両側の山に食い込むように立っています。ダムの真下から見上げたときに、壁がこちらに覆いかぶさってくるように見えるのはアーチ式の特徴です。</p>

  <h2>ダムを見るときに知っておきたい言葉</h2>
  <table>
    <tr><th>堤体（ていたい）</th><td>水をせき止めているダムの本体のことです</td></tr>
    <tr><th>天端（てんば）</th><td>ダムのいちばん上の部分です。歩いて渡れるダムも多くあります</td></tr>
    <tr><th>堤高（ていこう）</th><td>基礎の岩盤から天端までの高さです。<a href="/ranking/">ランキング</a>はこの数字で並べています</td></tr>
    <tr><th>堤頂長（ていちょうちょう）</th><td>天端の長さです</td></tr>
    <tr><th>洪水吐き（こうずいばき）</th><td>大雨のときに、ためきれない水を安全に下流へ流すための設備です。ゲートが並んでいるところがよく目立ちます</td></tr>
    <tr><th>減勢工（げんせいこう）</th><td>ダムから流れ落ちた水の勢いを弱めるために、ダムの下に造られる設備です</td></tr>
    <tr><th>ダム湖</th><td>ダムによってできた湖です。名前がつけられていることが多く、観光地になっている湖もあります</td></tr>
  </table>

  <h2>なぜダムによって形式が違うの？</h2>
  <p>ダムの形式は、見た目の好みで決まるのではなく、その場所の条件に合わせて選ばれます。いちばん大きな条件は、<strong>谷の形</strong>と<strong>地盤</strong>と<strong>材料</strong>です。</p>
  <ul>
    <li><strong>谷が深くて狭く、両岸が固い岩</strong>なら、少ないコンクリートで高いダムを造れるアーチ式が向いています。黒部ダムは、黒部峡谷の深い谷に造られたアーチ式です</li>
    <li><strong>地盤がそれほど固くない、または谷の幅が広い</strong>場合は、重さで支える重力式や、岩を積み上げるロックフィルが選ばれます</li>
    <li><strong>近くで大量の岩が取れる</strong>場所では、その岩を材料に使えるロックフィルが有利です。材料を遠くから運ばずに済むからです</li>
  </ul>
  <p>たとえば、北アルプスの深い峡谷にある黒部ダムはアーチ式、首都圏の丘陵地に近い宮ヶ瀬ダムは重力式、岩の材料が豊富な揖斐川の上流にある徳山ダムはロックフィルです。</p>
  <p>同じ川でも、上流と下流で形式の違うダムが並んでいることがあります。その場所ごとに、いちばん安全で無理のない形が選ばれた結果です。</p>

  <h2>形式ごとの見学の楽しみ方</h2>
  <h3>アーチ式</h3>
  <p>ダムの下流側から見上げると、薄い壁が弓なりに曲がって両側の山に食い込んでいる様子がよくわかります。ダムの上を歩くと、上流側にふくらんだカーブを足元で感じられます。</p>
  <h3>重力式</h3>
  <p>まっすぐ続く天端と、下流側の急な斜面が特徴です。ゲートがずらりと並ぶ洪水吐きや、観光放流で水が流れ落ちる様子は、重力式ならではの迫力があります。<a href="/dam/miyagase/">宮ヶ瀬ダム</a>では、ダムの上と下をインクラインやエレベーターで行き来できます。</p>
  <h3>ロックフィル</h3>
  <p>石がきれいに積み上げられた斜面は、近くで見ると一つ一つの石の大きさに驚かされます。なだらかな斜面と、広いダム湖が一緒に見渡せる景色が魅力です。</p>

  <h2>形式ごとの代表的なダム</h2>
  <p>日本の高いダム上位50から、形式ごとに高い順に6基ずつ選びました。同じ形式でも、高さと長さのバランスがダムによって違うことがわかります。</p>
{rep}
  <h2>ほかの形式</h2>
  <ul>
    <li><strong>重力式アーチダム</strong>：重力式とアーチ式の両方の仕組みで水を支える形式です。アーチ式より厚みがあります</li>
    <li><strong>中空重力式</strong>：重力式の中を空洞にして、コンクリートの量を減らしたものです</li>
    <li><strong>アースダム</strong>：土を盛って造るダムです。農業用のため池などに多い形式です</li>
    <li><strong>台形CSGダム</strong>：現地の土砂にセメントと水をまぜた材料で、台形に造る比較的新しい形式です</li>
  </ul>

  <h2>形式を知るとダム巡りが楽しくなる理由</h2>
  <p>同じ「ダム」でも、形式が違うと見た目も、見どころも、ダムの上からの景色もまったく違います。アーチ式は優美な曲線、重力式はどっしりとした迫力、ロックフィルは自然の山のような雄大さが魅力です。ダムカードのうら面にも形式が書かれているので、集めたカードを形式ごとに分けてみるのもおすすめです。→ <a href="/dam-card/">ダムカードのもらい方</a></p>
{SOURCE_HTML}"""
    write("/keishiki/", page("ダムの形式の見分け方｜アーチ式・重力式・ロックフィル｜ダム.com", "ダムの主な形式（アーチ式、重力式、ロックフィル）の違いと見分け方を、日本の高いダムの例とあわせて紹介します。", "/keishiki/", body, [("ダム.com", "/"), ("ダムの形式", None)]))
    count += 1

    # sitemap
    urls = ["/", "/dam-card/", "/kurobe/", "/ranking/", "/keishiki/", "/houryu/"] + [f"/keishiki/{t}/" for t in ["arch","gravity","rockfill"]] + [r["url"] for r in rows if r["has_page"] and r["slug"] != "kurobe"]
    known = {r["slug"] for r in rows}
    for extra in sorted(os.listdir(os.path.join(ROOT, "dam"))):  # 上位50以外の手書きページ
        if extra not in known and os.path.exists(os.path.join(ROOT, "dam", extra, "index.html")):
            urls.append(f"/dam/{extra}/")
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>https://xn--6ck4c.com{u}</loc><lastmod>{DATE}</lastmod></url>\n" for u in urls) + "</urlset>\n"
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    print("generated", count, "pages; sitemap urls", len(urls))

if __name__ == "__main__":
    main()
