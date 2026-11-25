#!/usr/bin/env python3
"""GitHub Actions で実行：Wikimedia Commons から「ダムカード」の画像を探し、
自由ライセンス（PD・CC0・CC BY・CC BY-SA）のものだけを tools/photos/cards.tsv に書き出す。"""
import os, re, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_photos import api, strip, ok_license, ROOT

CATS = ["Category:Dam cards", "Category:Dam cards of Japan", "Category:ダムカード"]
SEARCHES = ["ダムカード", "dam card japan", "damcard"]

def files():
    seen, out = set(), []
    for c in CATS:
        d = api("commons.wikimedia.org", {"action": "query", "list": "categorymembers", "cmtitle": c, "cmtype": "file|subcat", "cmlimit": 200})
        for m in d.get("query", {}).get("categorymembers", []):
            t = m["title"]
            if t.startswith("Category:") and t not in CATS:
                CATS.append(t)
            elif t.startswith("File:") and t not in seen:
                seen.add(t); out.append(t)
    for q in SEARCHES:
        d = api("commons.wikimedia.org", {"action": "query", "list": "search", "srsearch": q, "srnamespace": 6, "srlimit": 100})
        for h in d.get("query", {}).get("search", []):
            t = h["title"]
            if t not in seen and re.search(r"(dam.?card|ダムカード)", t, re.I):
                seen.add(t); out.append(t)
    return [f for f in out if re.search(r"\.(jpe?g|png)$", f, re.I)]

def main():
    out = ["file\tthumb_url\tfile_page_url\tauthor\tlicense\tlicense_url\ttitle"]
    fl = files()
    print("candidates:", len(fl))
    for f in fl[:150]:
        d = api("commons.wikimedia.org", {"action": "query", "titles": f, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 640})
        for p in d.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii:
                continue
            md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            if not ok_license(lic) or ii.get("width", 0) < 300:
                print("skip:", f, lic); continue
            title = re.sub(r"\.(jpe?g|png)$", "", f[5:], flags=re.I).replace("_", " ")
            out.append("\t".join([f, ii.get("thumburl") or ii.get("url"), ii.get("descriptionurl", ""),
                                  (strip(md.get("Artist", {}).get("value", "")) or "不明").replace("\t", " "),
                                  strip(lic), md.get("LicenseUrl", {}).get("value", ""), title.replace("\t", " ")]))
            print("ok:", f, lic)
        time.sleep(0.2)
    open(os.path.join(ROOT, "tools/photos/cards.tsv"), "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
